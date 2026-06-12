from ninja import NinjaAPI
from ninja.errors import ValidationError
from django.utils import timezone
from django.db import models
from django.db.models import Count
from datetime import timedelta
from .schema import ErrorResponse, SuccessResponse, CreateJob, ListJob, MetaPaginatedResponse, DLQ
from .models import Job, PriorityChoice, StatusChoices, DeadLetterQueue, IntervalChoices
from .town_crier import broadcast_event
import logging
import uuid
import math

logger = logging.getLogger(__name__)
api = NinjaAPI()

@api.exception_handler(ValidationError)
def handle_validation_errors(request, exc):
    return api.create_response(
        request, 
        ErrorResponse(message="Validation Error", error=str(exc.errors)
        ), status=422
    )

@api.post("/jobs", response={200: SuccessResponse, 400: ErrorResponse, 422: ErrorResponse, 500: ErrorResponse})
def create_job(request, payload: CreateJob):
    try:
        current_time = timezone.now()
        job_type = payload.type
        priority = payload.priority if payload.priority is not None else PriorityChoice.LOW
        job_payload = payload.payload
        scheduled_at = payload.scheduled_at or current_time
        interval = payload.interval

        # check if payload.scheduled_at is timezone aware
        if timezone.is_naive(scheduled_at):
            scheduled_at = timezone.make_aware(scheduled_at)
        
        if scheduled_at < (current_time - timedelta(minutes=1)):
            logger.error(f"scheduled time is smaller than current timezone time, scheduled_time: {scheduled_at}, current_timezone_time: {timezone.now()}")
            return 400, ErrorResponse(message="Bad Request", error="Scheduled date must be greater than current date")
        
        deps = []
        if len(payload.dependencies) > 0:
            deps = Job.objects.filter(id__in=payload.dependencies)
            list_deps = list(deps)
            logger.info("got here x2", extra={"deps": deps})
            if len(deps) != len(payload.dependencies):
                legal_deps = {dep.id for dep in list_deps}
                missing_deps = [dep for dep in payload.dependencies if dep not in legal_deps]
                logger.info("invalid ID among payload dependencies", extra={"payload_dep_len": len(payload.dependencies), "database_dep_len": len(list_deps), "missing": missing_deps})
                return 400, ErrorResponse(message="Bad Request", error=f"Unknown dependencies ID entered: {missing_deps}")
            
        logger.info("Job creation initiated.")
        job = Job.objects.create(type= job_type, priority= priority, mutated_priority= priority, payload= job_payload, scheduled_at= scheduled_at, interval = interval)
        logger.info("got here x4", extra={"deps": deps})
        if len(payload.dependencies) > 0:
            logger.info("got here x5", extra={"deps": deps})
            job.dependencies.set(deps)
        data = ListJob.model_validate(job)
        broadcast_event("job_created", job.id, job.status, job.retry_count)
        return 200, SuccessResponse(data=data)
    
    except Exception as e:
        print(e)
        logger.error("a server error occurred!", extra={"error": str(e)})
        return 500, ErrorResponse(message="Internal server error", error=str(e))
    
# Get all jobs
@api.get("/jobs", response={200: MetaPaginatedResponse, 422: ErrorResponse, 500: ErrorResponse})
def return_all_jobs(request, limit: int = 15, page: int = 1, status: str | None = None):
    try:
        jobs = Job.objects.all()
        if status:
            jobs = jobs.filter(status=status)

        minimum_data = (page - 1) * limit
        maximum_data = page * limit
        data = [ ListJob.model_validate(job) for job in jobs ]
        total_pages = math.ceil(len(data) / limit)
        paginated_data = data[minimum_data: maximum_data]
        logger.info("fetched all jobs successfully", extra={"jobs_length": jobs.count(), "limit": limit, "page": page})
        return 200, MetaPaginatedResponse(total_pages=total_pages, current_page=page, limit=limit, data=paginated_data)
    except Exception as e:
        logger.info("failed to fetch all jobs", extra={"error": str(e)})
        return 500, ErrorResponse(message="Internal Server Error", error=str(e))
    

# Get a single Job
@api.get("/jobs/{job_id}", response={200: SuccessResponse, 404: ErrorResponse, 422: ErrorResponse, 500: ErrorResponse})
def get_single_job(request, job_id: uuid.UUID):
    try:
        job = Job.objects.get(id=job_id)
        data = ListJob.model_validate(job)
        logger.info("fetched job successfully", extra={"job_id": job_id})
        return 200, SuccessResponse(data=data)
    except Job.DoesNotExist:
        logger.info("failed to find job with provided ID", extra={"provided_id": job_id})
        return 404, ErrorResponse(message="Not Found", error=f"Job with ID: {job_id} not found")
    except Exception as e:
        logger.info("failed to fetch job", extra={"provided_id": job_id})
        return 500, ErrorResponse(message="Internal Server Error", error=str(e))

    
# Cancel a job
@api.patch("/jobs/{job_id}/cancel", response={200: dict, 404: ErrorResponse, 422: ErrorResponse, 500: ErrorResponse})
def cancel_job(request, job_id: uuid.UUID):
    try:
        # Get job
        job = Job.objects.get(id=job_id)
        # Update job
        job.is_cancel_requested = True
        job.status = StatusChoices.CANCELLED
        job.save(update_fields=["is_cancel_requested", "status", "updated_at"])
        broadcast_event("job_cancelled", job.id, job.status, job.retry_count)
        return 200, {"status": "success", "message": "Job cancelled successfully"}
    except Job.DoesNotExist:
        logger.info("failed to retry job with provided ID (does not exist)", extra={"provided_id": job_id})
        return 404, ErrorResponse(message="Not Found", error=f"Job with ID: {job_id} not found")
    except Exception as e:
        logger.info("failed to retry job", extra={"provided_id": job_id})
        return 500, ErrorResponse(message="Internal Server Error", error=str(e))

@api.get("/dlq", response={200: SuccessResponse, 500: ErrorResponse})
def get_all_dlq_entry(request):
    try:
        entries = DeadLetterQueue.objects.all()
        data = [ DLQ.model_validate(entry) for entry in entries]
        logger.info("fetched all entries from dlq successfully", extra={"dlq_length": entries.count()})
        return 200, SuccessResponse(data=data)
    except Exception as e:
        logger.info("failed to fetch all entries from dlq", extra={"error": str(e)})
        return 500, ErrorResponse(message="Internal Server Error", error=str(e))

# Retry a job
@api.put("/dlq/{dlq_id}/retry", response={200: dict, 404: ErrorResponse, 422: ErrorResponse, 500: ErrorResponse})
def retry_failed_job(request, dlq_id: uuid.UUID):
    try:
        # Get Dead letter queue entry
        dlq = DeadLetterQueue.objects.get(id=dlq_id)
        # Get job
        job = dlq.job
        # Update job
        job.status = StatusChoices.PENDING
        job.processed_at = None
        job.scheduled_at = timezone.now()
        job.retry_count = 0
        job.save()
        broadcast_event("job_retried", job.id, job.status, job.retry_count)
        return 200, {"status": "success", "message": "Job retried successfully"}
    except DeadLetterQueue.DoesNotExist:
        logger.info("failed to retry job with provided ID (does not exist)", extra={"provided_id": dlq_id})
        return 404, ErrorResponse(message="Not Found", error=f"Dead  letter entry with ID: {dlq_id} not found")
    except Exception as e:
        logger.info("failed to retry job", extra={"provided_id": dlq_id, "error": str(e)})
        return 500, ErrorResponse(message="Internal Server Error", error=str(e))
    

@api.get("/stats", response={200: dict, 500: ErrorResponse})
def get_stats(request):
    try:
        stats = Job.objects.aggregate(
            total = Count("id"),
            pending = Count("id", filter=models.Q(status=StatusChoices.PENDING)),
            processing = Count("id", filter=models.Q(status=StatusChoices.PROCESSING)),
            completed = Count("id", filter=models.Q(status=StatusChoices.COMPLETED)),
            cancelled = Count("id", filter=models.Q(status=StatusChoices.CANCELLED)),
            failed = Count("id", filter=models.Q(status=StatusChoices.FAILED))
        )
        dlq_count = DeadLetterQueue.objects.filter(resolved=False).count()
        stats["dlq"] = dlq_count
        return 200, {
            "status": "success",
            "data" : stats
        }
    except Exception as e:
        logger.error("failed to fetch job stats", extra={"error": str(e)})
        return 500, ErrorResponse(message="Internal Server Error", error=str(e))
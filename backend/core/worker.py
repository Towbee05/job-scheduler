from datetime import timedelta
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from .handler import Handler
from .models import Job, StatusChoices, DeadLetterQueue
from .town_crier import broadcast_event
import logging
import random

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
DLQ_THRESHOLD = 10
BACKOFF_SECONDS = {
    1: 1,
    2: 5,
    3: 25,
}
MINUTES_IN_SECS = 60
RECURRING_MAP = {
    "every_1_minute": MINUTES_IN_SECS,
    "every_5_minutes": MINUTES_IN_SECS * 5,
    "every_1_hour": MINUTES_IN_SECS * 60
}
handler = Handler()

def handle_job_type(job):
    if job.type == "send_email":
        broadcast_event("job_processing", job.id, job.status, job.retry_count)
        handler.simulate_email_delivery(job.id, job.payload)
    else:
        logger.info("No handler for provided job type yet", extra={"job_type": job.type})
        

def backoff_calculator(attempt):
    base_delay = BACKOFF_SECONDS.get(attempt, BACKOFF_SECONDS[MAX_RETRIES])
    actual_delay = base_delay * 2 ** attempt
    jitter = random.uniform(0.8, 1.2)
    return actual_delay * jitter

def is_job_claimed(job):
    updated_job = Job.objects.filter(id=job.id, status=StatusChoices.PENDING).update(
        status=StatusChoices.PROCESSING,
        processed_at=timezone.now(),
    )
    job_is_claimed = updated_job == 1
    return job_is_claimed

def handle_error(job, error: Exception):
    job.retry_count += 1
    job.processed_at = timezone.now()
    if job.retry_count >= MAX_RETRIES:
        job.status = StatusChoices.FAILED
        job.save(update_fields=["retry_count", "processed_at", "status", "updated_at"])
        push_to_dead_queue(job, error)
    else:
        job.status=StatusChoices.PENDING
        delay = backoff_calculator(job.retry_count)
        scheduled_time = timezone.now() + timedelta(seconds=delay)
        job.scheduled_at = scheduled_time
        job.save(update_fields=["retry_count", "processed_at", "status", "scheduled_at", "updated_at"])
        logger.info("retrying task at backoff time", extra={"job_id": job.id, "backoff_time": delay, "scheduled_time": scheduled_time})

def push_to_dead_queue(job, error: Exception):
    dlq, _ = DeadLetterQueue.objects.update_or_create(
        job=job,
        defaults={"error": error.__str__(), "resolved": False},
    )
    logger.info("pushed job into dead letter queue", extra={"job_id": job.id})
    # check if threshold is passed
    unresolved = DeadLetterQueue.objects.filter(resolved=False).count()
    if unresolved >= DLQ_THRESHOLD: 
        logger.warning("Dead Letter Queue threshold is reached", extra={"unresolved": unresolved})
        dlq_payload = {
            "to": "olatiseoluwatobiloba@gmail.com",
            "subject": "Dead Letter Queue already exceeded threshold",
            "body": f"Dead Letter Queue is currently having {unresolved} unresolved jobs. Please check it out."
        }
        try:
            handler.simulate_email_delivery(job.id, dlq_payload)
        except Exception as alert_error:
            logger.error("failed to send dead letter queue alert", extra={
                "job_id": job.id,
                "error": alert_error.__str__(),
            })

def handle_recurring_jobs(job):
    # recurring jobs
    seconds = RECURRING_MAP.get(job.interval, None)
    if seconds is None:
        logger.warning("Unknown interval was provided", extra={"job_id": job.id, "provided_interval": job.interval})
        return
    next_schedule = timezone.now() + timedelta(seconds=seconds)
    job = Job.objects.create(type=job.type, priority=job.priority, mutated_priority=job.mutated_priority, payload=job.payload, scheduled_at= next_schedule, interval=job.interval)
    logger.info("scheduled recurring job", extra={"job_id": job.id, "job_type": job.type, "next_running_time": next_schedule})

def main(job):
    start_time = timezone.now().time()
    logger.info(f"Job started", extra={"job_id": job.id, "start_time": start_time, "type": job.type})

    # Ensure job is claimed by only one worker
    if not is_job_claimed(job):
        logger.info("job is claimed by some worker", extra={"job_id": job.id})
        return
    
    # Make sure job is in sync with db
    job.refresh_from_db()
    # check for requested cancellation
    if job.is_cancel_requested:
        job.status = StatusChoices.CANCELLED
        job.save()
        logger.info("Job cancelled", extra={"job_id": job.id, "job_type": job.type})
        broadcast_event("job_cancelled", job.id, job.status, job.retry_count)
        return 
    
    # Forward type to handler
    try:
        handle_job_type(job)
        # job completed successfully
        # check if job id in dead letter queue and mark as resolved
        try:
            dlq = DeadLetterQueue.objects.get(job__id=job.id)
            dlq.resolved = True
            dlq.save()
            broadcast_event("job_resolved", job.id, job.status, job.retry_count)
        except DeadLetterQueue.DoesNotExist:
            pass   
        job.status = StatusChoices.COMPLETED
        job.processed_at = timezone.now()
        job.save(update_fields=["status", "processed_at", "updated_at"])
        broadcast_event("job_completed", job.id, job.status, job.retry_count)
        logger.info("Job handled completely", extra={"job_id": job.id, "processed_at": job.processed_at})

        # If job is recurring
        if job.interval:
            handle_recurring_jobs(job)
    
    except Exception as e:
        try:
            handle_error(job, e)
            broadcast_event("job_failed_and_retried", job.id, job.status, job.retry_count)
        except Exception as error_handler_failure:
            logger.error("failed to handle job error", extra={
                "job_id": job.id,
                "original_error": str(e),
                "error_handler_failure": str(e),
            })
            Job.objects.filter(id=job.id, status=StatusChoices.PROCESSING).update(
                status=StatusChoices.FAILED,
                processed_at=timezone.now(),
            )
            broadcast_event("job_failed", job.id, job.status, job.retry_count)
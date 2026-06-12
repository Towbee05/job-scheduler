from .models import Job, StatusChoices
from .heap import JobHeap
from django.utils import timezone
from .worker import push_to_dead_queue
from datetime import timedelta
import time
import logging

logger = logging.getLogger(__name__)
RESTART_THRESHOLD_IN_MINS = 5
AGING_INTERVAL = 60
MIN_PRIORITY = 1

job_heap = JobHeap()
def restart_stuck_jobs():
    stuck_time = timezone.now() - timedelta(minutes=RESTART_THRESHOLD_IN_MINS)
    stuck_jobs = Job.objects.filter(processed_at__lte= stuck_time, status=StatusChoices.PROCESSING)
    if stuck_jobs.count() > 0:
        logger.info("Restarted staled jobs", extra={"number_of_stale_jobs": stuck_jobs.count()})
        stuck_jobs.update(
            status=StatusChoices.PENDING,
            processed_at=None
        )

def allocator():
    # Check for stale jobs and restart these jobs
    restart_stuck_jobs()

    # Get all pending requests
    pending_jobs = Job.objects.filter(status=StatusChoices.PENDING, scheduled_at__lte=timezone.now()).prefetch_related("as_child__parent_job")
    position = 0
    if pending_jobs.count() > 0:
        for job in pending_jobs:
            # priority aging logic -> starved jobs
            now = timezone.now()
            wait_seconds = (now - job.scheduled_at).total_seconds()
            age_step = int(wait_seconds // AGING_INTERVAL)

            if age_step > 0:
                new_priority = max(MIN_PRIORITY, job.priority - age_step)
                if job.mutated_priority != new_priority:
                    job.mutated_priority = new_priority
                    job.save(update_fields=['mutated_priority'])
                    logger.info("decreased the mutated priority of a job", extra={"job_id": job.id, "wait_time": wait_seconds, "mutated_priority": new_priority})

            dependencies = job.as_child.all()
            all_dep_complete = all(
                dep.parent_job.status == StatusChoices.COMPLETED
                for dep in dependencies
            )
            if all_dep_complete:
                logger.info("Pushed job into priority heap", extra={"job_id": job.id, "position": position})
                job_heap.push(job)
                position += 1
            else:
                pending_dependencies = [dep for dep in dependencies if dep.parent_job.status == StatusChoices.PENDING]
                completed_dependencies = dependencies.filter(parent_job__status=StatusChoices.COMPLETED)
                processing_dependencies = dependencies.filter(parent_job__status=StatusChoices.PROCESSING)
                failed_dependencies = dependencies.filter(parent_job__status=StatusChoices.FAILED)
                if failed_dependencies.exists():
                    job.status= StatusChoices.FAILED
                    job.save()
                    # Add to dead letter queue
                    push_to_dead_queue(job, Exception("Dependency failed: parent job(s) did not complete"))
                    logger.warning("Cancelled job because a dependency failed", extra={
                    "job_id": job.id, "failed_dependencies": failed_dependencies.count()})
                else:
                    logger.warning("Skipping job, dependency not ready", extra={
                        "job_id": job.id, 
                        "pending_dependencies": pending_dependencies.count(), 
                        "completed_dependencies": completed_dependencies.count(),
                        "processing_dependencies": processing_dependencies.count(),
                        "failed_dependencies": failed_dependencies.count()
                        })
        logger.info("Pushed all jobs into heap", extra={"heap_size": position})
    return job_heap
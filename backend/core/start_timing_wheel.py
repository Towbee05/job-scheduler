from .timing_wheel import TimingWheel, WHEEL_SLOT_COUNT
from .worker import main
from .models import Job, StatusChoices
import time
import logging

logger = logging.getLogger(__name__)
REFRESH_JOBS_INTERVAL = 10 #in seconds
def start_timing_wheel(wheel: TimingWheel, executor):
    logger.info("starting timing wheel", extra={"slot_count": WHEEL_SLOT_COUNT})
    tick = 0
    while True:
        try:
            if tick % REFRESH_JOBS_INTERVAL == 0:
                pending_jobs = Job.objects.filter(status=StatusChoices.PENDING)
                for job in pending_jobs:
                    wheel.add_job(job)
            due_jobs = wheel.tick()
            for job in due_jobs:
                logger.info("timing wheel dispatching", extra={"job_id": str(job.id)})
                executor.submit(main, job)
        except Exception as e:
            logger.error("timing wheel encountered error", extra={"error": str(e)})
        time.sleep(1)

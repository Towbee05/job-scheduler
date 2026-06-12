import time
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from django.core.management import BaseCommand
from django.utils import timezone
from ...worker_pool import start_worker_pool
from ...timing_wheel import TimingWheel
from ...models import Job, StatusChoices
from ...start_timing_wheel import start_timing_wheel

MAX_WORKERS = 3

logger = logging.getLogger(__name__)
timing_wheel = TimingWheel()

class Command(BaseCommand):
    help = "Worker starting outside the main application to handle scheduled task runs"
    
    def handle(self, *args, **kwargs):
        pending_jobs = Job.objects.filter(status=StatusChoices.PENDING)
        executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
        for job in pending_jobs:
            timing_wheel.add_job(job)
        logger.info("timing_wheel_seeded", extra={"count": pending_jobs.count()})

        heap_thread = threading.Thread(target=start_worker_pool, args=(executor, ), daemon=True, name="heap_handler")
        wheel_thread = threading.Thread(target=start_timing_wheel, args= (timing_wheel, executor), daemon=True, name="timing_wheel_handler")

        heap_thread.start()
        wheel_thread.start()

        logging.info("Worker started", extra={"timestamp": timezone.now().timestamp()})
        self.stdout.write("Worker started")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stdout.write("Shutting down.")
            logger.info("Worker shutdown")
        finally:
            executor.shutdown(wait=True)
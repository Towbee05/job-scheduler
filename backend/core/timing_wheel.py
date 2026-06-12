from collections import defaultdict
from django.utils import timezone
from .models import Job, StatusChoices
import threading
import time
import logging

logger = logging.getLogger(__name__)

WHEEL_SLOT_COUNT = 60
class TimingWheel:
    def __init__(self):
        self.wheel = defaultdict(list)
        self.overflow = []
        self.current_slot = int(time.time()) % WHEEL_SLOT_COUNT
        self.item_in_wheel_set = set()
        self._lock = threading.Lock()

    def _get_job_slot(self, scheduled_at):
        return int(scheduled_at.timestamp()) % WHEEL_SLOT_COUNT
    
    def add_job(self, job):
        # add job to wheel
        with self._lock:
            if job.id in self.item_in_wheel_set:
                return
            
            now = timezone.now()
            total_second = (job.scheduled_at - now).total_seconds()

            if total_second > WHEEL_SLOT_COUNT:
                # job is farther than 60secs in future
                self.overflow.append(job.id)
                # logger.info("job added to overflow", extra={
                #     "job_id": str(job.id),
                #     "total_seconds": round(total_second, 2)
                # })
            else:
                slot = self._get_job_slot(job.scheduled_at)
                self.wheel[slot].append(job.id)
                logger.info("job added to slot", extra={ "job_id": str(job.id), "slot": slot})
            self.item_in_wheel_set.add(job.id)

    def _move_overflow_to_slot(self):
        now = timezone.now()
        still_overflow = []

        for id in self.overflow:
            try:
                job = Job.objects.get(id=id)
                total_seconds = (job.scheduled_at - now).total_seconds()

                if total_seconds > WHEEL_SLOT_COUNT:
                    still_overflow.append(id)
                else:
                    slot = self._get_job_slot(job.scheduled_at)
                    self.wheel[slot].append(id)
                    logger.info("job promoted to slot", extra={ "job_id": str(job.id), "slot": slot})

            except Job.DoesNotExist:
                pass
        self.overflow = still_overflow

    def tick(self):
        with self._lock:
            self._move_overflow_to_slot()
            due_jobs_ids = self.wheel.pop(self.current_slot, [])
            self.current_slot = int(time.time()) % WHEEL_SLOT_COUNT
        due_jobs = []
        for id in due_jobs_ids:
            self.item_in_wheel_set.discard(id)
            try:
                job = Job.objects.get(id=id, status=StatusChoices.PENDING)
                if job.scheduled_at <= timezone.now():
                    due_jobs.append(job)
                else:
                    self.add_job(job)
                logger.debug("timing_wheel_fired_job", extra={
                    "job_id": str(id),
                    "slot": self.current_slot
                })
            except Job.DoesNotExist:
                pass

        return due_jobs
    
    def __len__(self):
        return sum(len(jobs) for jobs in self.wheel.values()) + len(self.overflow)
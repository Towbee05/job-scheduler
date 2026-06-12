from .models import Job
import heapq
import logging

logger = logging.getLogger(__name__)
class JobHeap:
    def __init__(self):
        self.heap_set = set()
        self.heap = []

    def push(self, job):
        if not job.id in self.heap_set:
            self.heap_set.add(job.id)
            heapq.heappush(self.heap, (
                job.mutated_priority,
                job.scheduled_at,
                job.created_at,
                job.id
            ))

    def pop(self):
        if not self.heap:
            return None
        removed_item =  heapq.heappop(self.heap)
        self.heap_set.remove(removed_item[3])
        job_id = removed_item[3]
        try:
            job = Job.objects.get(id=job_id)
            return job
        except Job.DoesNotExist:
            logger.error("Job with ID does not exist", extra={"job_id": job_id})
            return None
    
    def __len__(self):
        return len(self.heap)
    
    def display_heap(self):
        for job in self.heap:
            logger.debug("heap_entry", extra={
                "priority": job[0],
                "scheduled_at": str(job[1]),
                "job_id": str(job[3])
            })

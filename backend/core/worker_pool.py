from concurrent.futures import Executor
from .worker import main
from .allocator import allocator
import logging
import time 

logger = logging.getLogger(__name__)
def start_worker_pool(executor: Executor):
    while True:
        try:
            heap = allocator()
            # pop from heap
            while len(heap) > 0:
                job = heap.pop()
                if job is None:
                    continue
                executor.submit(main, job)
        except Exception as e:
            logger.error("error in worker pool", extra={"error": str(e)})
        time.sleep(1)
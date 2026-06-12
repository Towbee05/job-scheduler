import time
import random
from datetime import timedelta
from django.utils import timezone
from .heap import JobHeap
from .timing_wheel import TimingWheel, WHEEL_SLOT_COUNT

def benchmark_heap(jobs):
    heap = JobHeap()

    start_time = time.perf_counter()
    for job in jobs:
        heap.push(job)
    insert_time = time.perf_counter() - start_time

    start_time = time.perf_counter()
    while len(heap) > 0:
        heap.pop()
    pop_time = time.perf_counter() - start_time

    return {
        "insert_time": insert_time,
        "pop_time": pop_time
    }


def benchmark_timing_wheel(jobs):
    wheel = TimingWheel()

    start_time = time.perf_counter()
    for job in jobs:
        wheel.add_job(job)
    insert_time = time.perf_counter() - start_time

    start_time = time.perf_counter()
    for _ in range(WHEEL_SLOT_COUNT):
        wheel.tick()
    tick_time = time.perf_counter() - start_time

    return {
        "insert_time": insert_time,
        "tick_time": tick_time
    }

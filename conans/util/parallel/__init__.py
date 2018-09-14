
import os
from contextlib import contextmanager

from conans.util.parallel.executor import TaskExecutor


@contextmanager
def parallel_tasks(n_threads=os.cpu_count()):
    parallelism_allowed = True

    if parallelism_allowed:
        executor = TaskExecutor(n_threads=n_threads)
        yield executor
        executor.terminate()

    else:
        class SerialQueue(object):
            def put(self, job):
                func, args = job
                self.add_task(func, args)

            def add_task(self, func, args):
                run_task(self, func, args)

        yield SerialQueue()
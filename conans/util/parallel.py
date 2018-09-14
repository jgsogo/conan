
import os
import time
from multiprocessing import Pool, JoinableQueue, Process, freeze_support
from contextlib import contextmanager


def task_sleep(msg, secs):
    print(msg)
    time.sleep(secs)
    if secs % 2 == 0:
        print("*"*20)
        return (task_sleep, ("-- recurrent --", 1)),


def run_task(task_queue, func, args):
    ret = func(*args)
    if ret:
        for new_func, new_args in ret:
            task_queue.put((new_func, new_args))


def worker(task_queue):
    for func, args in iter(task_queue.get, 'STOP'):
        print("\t{}: {}({})".format(os.getpid(), func.__name__, ', '.join(map(str, args))))
        try:
            run_task(task_queue, func, args)
            print("--")
        finally:
            task_queue.task_done()
    print("worker end...")


class Executor(object):
    def __init__(self, n_threads=os.cpu_count()):
        self._task_queue = JoinableQueue()
        self._processes = [Process(target=worker, args=(self._task_queue, )) for _ in range(
            n_threads)]
        for it in self._processes:
            it.start()

    def add_task(self, func, *args):
        self._task_queue.put((func, *args))

    def terminate(self):
        self._task_queue.join()
        for _ in range(len(self._processes)):
            self._task_queue.put('STOP')


@contextmanager
def parallel_tasks(n_threads=os.cpu_count()):
    parallelism_allowed = True
    if parallelism_allowed:
        executor = Executor(n_threads=n_threads)
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


if __name__ == '__main__':
    # freeze_support()

    with parallel_tasks(10) as executor:
        print(">> Send task task1")
        executor.add_task(task_sleep, ("task1", 2))

        print(">> Send task task2")
        executor.add_task(task_sleep, ("task2", 1))

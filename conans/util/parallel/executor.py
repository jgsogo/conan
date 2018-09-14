
import os
from uuid import uuid1
from multiprocessing import Pool, JoinableQueue, Process, Queue

from conans.util.parallel.logger import logger_worker
from conans.util.parallel.worker import worker


class TaskExecutor(object):

    def __init__(self, n_threads):
        self._processes = []
        self._ret_queue = Queue()
        self._ret_data = {}

        # Initialize logger worker
        self._logger_queue = Queue()
        p = Process(target=logger_worker, args=(self._logger_queue, ))
        p.start()
        self._processes.append(p)

        # Initialize task workers
        self._task_queue = JoinableQueue()
        for _ in range(n_threads):
            p = Process(target=worker, args=(self._task_queue, self._ret_queue,
                                             self._logger_queue, ))
            p.start()
            self._processes.append(p)

    def add_task(self, func, kwargs, on_done=None, on_done_kwargs=None):
        """
        Add task for multithreading execution
        :param func: function to execute in thread
        :param args: args in the call to 'func' (must be pickleable)
        :param on_done: function to execute in main thread afterwards
        :param on_done_kwargs: kwargs for 'on_done' function.
        :return:
        """
        task_id = uuid1()
        self._ret_data[task_id] = (on_done, on_done_kwargs)
        self._task_queue.put((task_id, func, kwargs))

    def terminate(self):
        # Stop all workers
        self._task_queue.join()
        for _ in range(len(self._processes)):
            self._task_queue.put_nowait(None)

        # Stop logger
        self._logger_queue.put_nowait(None)

        # Consume the remaining
        self.consume_ret_task()
        assert len(self._ret_data) == 0

    def consume_ret_task(self):
        if len(self._ret_data):
            try:
                while True:
                    ret = self._ret_queue.get_nowait()
                    task_id, ret_kwargs = ret
                    on_done, on_done_kwargs = self._ret_data.pop(task_id)
                    if on_done:
                        z = ret_kwargs if ret_kwargs else dict()
                        if on_done_kwargs:
                            z.update(on_done_kwargs)
                        on_done(**z)
            except Queue.Empty:
                pass

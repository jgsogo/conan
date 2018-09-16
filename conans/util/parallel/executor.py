
import os
from uuid import uuid1
from multiprocessing import Pool, JoinableQueue, Process, Queue
from multiprocessing.queues import Empty
from contextlib import contextmanager

from conans.util.parallel.logger import logger_worker
from conans.util.parallel.worker import worker
from conans.util.log import logger


class TaskGroupExecutor(object):
    def __init__(self, task_queue, ret_queue, ret_data, id):
        self._task_queue = task_queue
        self._ret_queue = ret_queue
        self._ret_data = ret_data
        self._my_tasks = set()
        self._output = {}
        self._id = id

    def __str__(self):
        return str(self._id)

    def add_task(self, func, kwargs, on_done=None, on_done_kwargs=None, task_id=None):
        """
        Add task for multithreading execution
        :param func: function to execute in thread
        :param kwargs: kwargs in the call to 'func' (must be pickleable)
        :param on_done: function to execute in main thread afterwards
        :param on_done_kwargs: kwargs for 'on_done' function.
        :return:
        """
        task_id = task_id or uuid1()
        assert task_id not in self._ret_data
        self._ret_data[task_id] = (on_done, on_done_kwargs)
        self._task_queue.put((task_id, func, kwargs))
        self._my_tasks.add(task_id)
        return task_id

    def _terminate(self, already_finished):
        # Consume all my tasks
        my_tasks = self._my_tasks.copy()
        self._my_tasks.difference_update(already_finished)
        my_tasks_consumed = self._consume_ret_task(block=True)
        assert self._done()
        my_tasks.update(my_tasks_consumed)
        return my_tasks, self._output

    def _consume_ret_task(self, block=False):
        my_tasks_consumed = set()
        while not self._done():
            try:
                task_id, ret_kwargs = self._ret_queue.get(block=block)
                on_done, on_done_kwargs = self._ret_data.pop(task_id)

                ret = None
                if isinstance(ret_kwargs, Exception):
                    # TODO: ??
                    pass
                elif on_done:
                    z = ret_kwargs if ret_kwargs else dict()
                    if on_done_kwargs:
                        z.update(on_done_kwargs)

                    try:
                        ret = on_done(**z)  # This can add new tasks at this task-group level!
                    except Exception as e:
                        ret = e

                self._output[task_id] = ret
                try:
                    self._my_tasks.remove(task_id)
                    my_tasks_consumed.add(task_id)
                except KeyError:
                    pass

            except Empty:
                break
        return my_tasks_consumed

    def _done(self):
        return len(self._my_tasks) == 0


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

        # Stack of task groups (and 'my' group)
        self._outermost_task_group = TaskGroupExecutor(task_queue=self._task_queue,
                                                       ret_queue=self._ret_queue,
                                                       ret_data=self._ret_data,
                                                       id="Outermost")
        self._task_group_stack = list()
        self._task_outputs = {}

    def add_task(self, *args, **kwargs):
        return self._outermost_task_group.add_task(*args, **kwargs)

    @contextmanager
    def task_group(self, output=None, id=None):
        task_group = TaskGroupExecutor(task_queue=self._task_queue, ret_queue=self._ret_queue,
                                       ret_data=self._ret_data, id=id)
        self._task_group_stack.append(task_group)
        try:
            yield task_group
        finally:
            task_group = self._task_group_stack.pop()
            tasks, outputs = task_group._terminate(already_finished=self._task_outputs.keys())
            self._task_outputs.update(outputs)
            this_outputs = {task: self._task_outputs.pop(task) for task in tasks}
            if output is not None:
                output.update(this_outputs)

    def _terminate(self):
        assert len(self._task_group_stack) == 0

        # Consume the remaining tasks
        self._outermost_task_group._terminate(already_finished=self._task_outputs.keys())
        assert len(self._task_outputs) == 0

        # Stop all workers
        self._task_queue.join()
        for _ in range(len(self._processes)):
            self._task_queue.put_nowait(None)

        # Stop logger
        self._logger_queue.put(None)

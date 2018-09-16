
import os
from uuid import uuid1
from multiprocessing import Pool, JoinableQueue, Process, Queue
from multiprocessing.queues import Empty
from contextlib import contextmanager

from conans.util.parallel.logger import logger_worker
from conans.util.parallel.worker import worker
from conans.util.log import logger


class Future(object):
    def __init__(self, task_id, task_group, executor):
        self._task_id = task_id
        self._task_group = task_group
        self._executor = executor

    def __str__(self):
        return '/'.join([str(self._task_group), self._task_id])

    @property
    def task_id(self):
        return self._task_id

    @property
    def task_group(self):
        return str(self._task_group)

    def result(self):
        return self._executor.wait_for(self._task_id, self._task_group)


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
        :param on_done: function to execute in main thread afterwards. Must accept, as arguments,
                the return values from 'func' if any.
        :param on_done_kwargs: kwargs for 'on_done' function
        :return:
        """
        task_id = task_id or uuid1()
        assert task_id not in self._ret_data
        self._ret_data[task_id] = (on_done, on_done_kwargs or {})
        self._task_queue.put((task_id, func, kwargs))
        self._my_tasks.add(task_id)
        return task_id

    def wait_for(self, task_id):
        if task_id not in self._output:
            assert task_id in self._my_tasks
            self._consume_tasks(block=True, list_to_consume={task_id, })
        return self._output[task_id]

    def _terminate(self, already_finished):
        # Consume all my remaining tasks
        self._my_tasks.difference_update(already_finished)
        self._consume_tasks(block=True)
        assert len(self._my_tasks) == 0
        return self._output

    def _consume_tasks(self, block=False, list_to_consume=None):
        list_to_consume = list_to_consume or self._my_tasks
        assert all([it not in self._output.keys() for it in list_to_consume])
        tasks_consumed = set()
        while list_to_consume:
            try:
                task_id, task_ret = self._ret_queue.get(block=block)
                on_done, on_done_kwargs = self._ret_data.pop(task_id)
                ret = task_ret
                if isinstance(task_ret, Exception):
                    # TODO: Task output is an exception, anything to do?
                    pass
                elif on_done:
                    on_done_args = list()
                    if isinstance(ret, dict):
                        on_done_kwargs.update(ret)
                    elif isinstance(ret, (list, tuple)):
                        on_done_args = ret
                    else:
                        on_done_args = (ret, )

                    try:
                        ret = on_done(*on_done_args, **on_done_kwargs)
                    except Exception as e:
                        ret = e
                self._output[task_id] = ret

                list_to_consume.discard(task_id)
                tasks_consumed.add(task_id)
            except Empty:
                break

        self._my_tasks.difference_update(tasks_consumed)
        return tasks_consumed


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

        # Storage for outputs
        self._task_outputs = {}

        # Stack of task groups
        self._task_group_stack = list()
        self._current_task_group = None
        self._current_tasks = set()

    def add_task(self, *args, **kwargs):
        task_id = self._current_task_group.add_task(*args, **kwargs)
        self._current_tasks.add(task_id)
        return Future(task_id=task_id, task_group=self._current_task_group, executor=self)

    def wait_for(self, task_id, task_group):
        if task_id not in self._task_outputs:
            return task_group.wait_for(task_id=task_id)
        else:
            return self._task_outputs[task_id]

    @contextmanager
    def task_group(self, id=None):
        self._task_group_stack.append((self._current_task_group, self._current_tasks))
        try:
            if self._current_task_group:
                id = '/'.join([str(self._current_task_group), id or ''])

            self._current_tasks = set()
            self._current_task_group = TaskGroupExecutor(task_queue=self._task_queue,
                                                         ret_queue=self._ret_queue,
                                                         ret_data=self._ret_data, id=id)

            yield

            outputs = self._current_task_group._terminate(already_finished=self._task_outputs.keys())
            self._task_outputs.update(outputs)
            # If we delete items in this dict, then futures won't get valid values from outside
            #   their context, yay or nay?
            # for t in self._current_tasks:  # Not really needed if we let _task_outputs to grow
            #     del self._task_outputs[t]
        finally:
            self._current_task_group, self._current_tasks = self._task_group_stack.pop()

    def _terminate(self):
        assert self._current_task_group is None
        assert len(self._task_group_stack) == 0
        # assert len(self._task_outputs) == 0

        # Stop all workers
        self._task_queue.join()
        for _ in range(len(self._processes)):
            self._task_queue.put_nowait(None)

        # Stop logger
        self._logger_queue.put(None)

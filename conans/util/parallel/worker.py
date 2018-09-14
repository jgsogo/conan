
import logging
from logging.handlers import QueueHandler


def _configure_worker_logger(log_queue):
    h = QueueHandler(log_queue)  # Just the one handler needed
    root = logging.getLogger()
    root.addHandler(h)
    # send all messages, for demo; no other level or filter logic applied.
    root.setLevel(logging.DEBUG)  # TODO: Default to Conan's one


def worker(task_queue, ret_queue, log_queue):
    _configure_worker_logger(log_queue)
    logger = logging.getLogger('conans')

    while True:
        task = task_queue.get()
        if task is None:  # We send this as a sentinel to tell the listener to quit
            break
        task_id, func, kwargs = task

        try:
            ret = func(logger=logger, **kwargs)
            ret_queue.put((task_id, ret))
        except Exception as e:
            import traceback
            logger.error("Error on task '{}':\n{}".format(task_id, traceback.format_exc()))
            ret_queue.put((task_id, e))
        finally:
            task_queue.task_done()

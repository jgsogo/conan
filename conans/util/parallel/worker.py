
import logging
# from conans.util.parallel.task import ConanTask


def _configure_worker_logger(log_queue):
    h = logging.handlers.QueueHandler(log_queue)  # Just the one handler needed
    root = logging.getLogger()
    root.addHandler(h)
    # send all messages, for demo; no other level or filter logic applied.
    root.setLevel(logging.DEBUG)  # TODO: Default to Conan's one


def worker(task_queue, ret_queue, log_queue, output_queue):
    _configure_worker_logger(log_queue)
    logger = logging.getLogger('conans')

    while True:
        task = task_queue.get()
        if task is None:  # We send this as a sentinel to tell the listener to quit
            break
        task_id, func, kwargs = task

        ret = None
        try:
            ret = func(logger=logger, **kwargs)
        except Exception as e:
            import sys, traceback
            logger.error('Whoops! Problem:\n{}'.format(traceback.format_exc()))
        finally:
            task_queue.task_done()
            ret_queue.put((task_id, ret))

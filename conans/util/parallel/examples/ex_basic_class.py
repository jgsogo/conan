
import time
import os
from conans.util.parallel import spawn_processes
from conans.util.log import logger, configure_logger


def _threaded_hard_task1(item, logger):
    time.sleep(int(item))
    print("\t Done _threaded_hard_task1(item='{}')".format(item))
    logger.info("--- log from inside threaded item='{}'".format(item))
    return {'msg': "_threaded_hard_task1(item='{}') done!".format(item)}


class MyStateClass(object):
    def __init__(self):
        pass

    def hard_task1(self, item, tasks):
        logger.info("> hard_task(item='{}')".format(item))
        return tasks.add_task(_threaded_hard_task1, {'item': item},
                              self.after_hard_task, {'original': item})

    def after_hard_task(self, msg, original):
        logger.info("> after_hard_task(msg='{}', original='{}')".format(msg, original))
        return original


if __name__ == '__main__':
    os.environ['CONAN_LOGGING_LEVEL'] = '10'
    logger = configure_logger()

    my_class = MyStateClass()
    with spawn_processes(2) as processes:
        with processes.task_group():
            for item in reversed(["1", "2"]):
                my_class.hard_task1(item, tasks=processes)

            # Add more tasks
            for item in reversed(["3", "4"]):
                my_class.hard_task1(item, tasks=processes)


import time
import os
from conans.util.parallel import parallel_tasks
from conans.util.log import logger, configure_logger


def _threaded_hard_task1(item, logger):
    if item == 'throw':
        raise ValueError("'{}' THROWS!!".format(item))
    return {'msg': "'{}' success!".format(item)}


class MyStateClass(object):
    def __init__(self):
        pass

    def hard_task1(self, item, executor):
        logger.info("> hard_task(item='{}')".format(item))
        executor.add_task(_threaded_hard_task1, {'item': item},
                          self.after_hard_task, {'original': item},
                          task_id='Task id unique %s' % item)

    def after_hard_task(self, msg, original):
        logger.info("> after_hard_task(msg='{}', original='{}')".format(msg, original))


if __name__ == '__main__':
    os.environ['CONAN_LOGGING_LEVEL'] = '10'
    logger = configure_logger()

    my_class = MyStateClass()
    with parallel_tasks(2) as executor:
        for item in ["ok", "throw"]:
            my_class.hard_task1(item, executor=executor)

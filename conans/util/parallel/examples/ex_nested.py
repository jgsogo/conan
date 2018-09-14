
import time
import os
from conans.util.parallel import parallel_tasks
from conans.util.log import logger, configure_logger


def _threaded_hard_task1(item, logger):
    time.sleep(int(item))
    print("\t Called _threaded_hard_task1(titem='{}')".format(item))
    logger.info("--- log from inside threaded titem='{}'".format(item))
    return {'msg': "_threaded_hard_task1(titem='{}') done!".format(item)}


class MyStateClass(object):
    def __init__(self):
        pass

    def hard_task1(self, item, executor):
        logger.info("> hard_task(item='{}')".format(item))
        executor.add_task(_threaded_hard_task1, {'item': item},
                          self.after_hard_task, {'original': item,
                                                 'executor': executor},
                          task_id='Task id unique %s' % item)

    def after_hard_task(self, msg, original, executor):
        logger.info("> after_hard_task(msg='{}', original='{}')".format(msg, original))

        # Do another hard_task
        executor.add_task(_threaded_hard_task1, {'item': "0"},
                          self.do_nothing, {'original': original},
                          task_id='Task for do_nothing %s' % original)

    def do_nothing(self, msg, original):
        logger.info("> do_nothing(original='{}')".format(original))


if __name__ == '__main__':
    os.environ['CONAN_LOGGING_LEVEL'] = '10'
    logger = configure_logger()

    my_class = MyStateClass()
    with parallel_tasks(2) as executor:
        for item in ["1", "2"]:
            my_class.hard_task1(item, executor=executor)

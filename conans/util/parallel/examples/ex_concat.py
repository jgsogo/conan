
import time
import os
from conans.util.parallel import spawn_processes
from conans.util.log import logger, configure_logger


def _threaded_hard_task1(item, logger):
    time.sleep(int(item))
    print("\t Called _threaded_hard_task1(item='{}')".format(item))
    logger.info("--- log from inside threaded item='{}'".format(item))
    return {'msg': "_threaded_hard_task1(item='{}') done!".format(item)}


class MyStateClass(object):
    def __init__(self):
        pass

    def hard_task1(self, item, tasks):
        logger.info("> hard_task(item='{}')".format(item))
        return tasks.add_task(_threaded_hard_task1, {'item': item},
                              self.after_hard_task, {'original': item,
                                                     'tasks': tasks},
                              task_id='Task id unique %s' % item)

    def after_hard_task(self, msg, original, tasks):
        logger.info("> after_hard_task(msg='{}', original='{}')".format(msg, original))

        # Do another hard_task
        t = tasks.add_task(_threaded_hard_task1, {'item': "0"},
                           self.do_nothing, {'original': original},
                           task_id='Task for do_nothing %s' % original)
        # return 23
        return t.result()

    def do_nothing(self, msg, original):
        logger.info("> do_nothing(original='{}')".format(original))
        return 42


if __name__ == '__main__':
    os.environ['CONAN_LOGGING_LEVEL'] = '10'
    logger = configure_logger()

    my_class = MyStateClass()
    t = None
    with spawn_processes(2) as processes:
        t = my_class.hard_task1("1", tasks=processes)

    print(t.result())

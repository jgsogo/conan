
import time
import os
from conans.util.parallel import parallel_tasks
from conans.util.log import logger, configure_logger


def _threaded_hard_task1(titem, logger):
    time.sleep(int(titem))
    print("\t Called _threaded_hard_task1(titem='{}')".format(titem))
    logger.info("--- log from inside threaded titem='{}'".format(titem))
    return {'msg': "_threaded_hard_task1(titem='{}') done!".format(titem)}


class MyStateClass(object):
    def __init__(self):
        pass

    def hard_task1(self, item, executor):
        logger.info("> hard_task(item='{}')".format(item))
        executor.add_task(_threaded_hard_task1, {'titem': item},
                          self.after_hard_task, {'original': item})

    def after_hard_task(self, msg, original):
        logger.info("> after_hard_task(msg='{}', original='{}')".format(msg, original))


if __name__ == '__main__':
    os.environ['CONAN_LOGGING_LEVEL'] = '10'
    logger = configure_logger()

    my_class = MyStateClass()
    with parallel_tasks(2) as executor:
        for item in reversed(["1", "2"]):
            my_class.hard_task1(item, executor=executor)

        # I can consume tasks before exiting the context scope
        time.sleep(1.5)
        executor.consume_ret_task()

        # Add more tasks
        for item in reversed(["3", "4"]):
            my_class.hard_task1(item, executor=executor)

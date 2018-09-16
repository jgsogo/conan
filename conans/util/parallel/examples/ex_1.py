import time
import os
from conans.util.parallel import spawn_processes
from conans.util.log import logger, configure_logger


def _sum(a, b, logger):
    logger.debug("_sum({}, {})".format(a, b))
    r = a + b
    return {'r': r}


def _div(a, b, logger):
    logger.debug("_div({}, {})".format(a, b))
    if b != 0:
        return {'r': a/b}
    else:
        logger.error("Divisor equals to 0")
        raise ValueError


def _nothing(a, b, logger):
    logger.debug("_nothing({}, {})".format(a, b))
    pass


def handle_result(operation, r):
    logger.info("Operation was '{}={}'".format(operation, str(r)))
    return r


if __name__ == '__main__':
    os.environ['CONAN_LOGGING_LEVEL'] = '50'
    logger = configure_logger()

    t = None
    with spawn_processes(3) as processes:
        # Adding tasks and returning func
        tasks = [processes.add_task(_sum, {'a': 2, 'b': it}) for it in range(4)]
        for it in tasks:
            print(it.result())

        # Adding tasks using a context function
        for item in range(2):

            def on_done(r):
                handle_result("sum(10, {})".format(item), r)
                return r

            t = processes.add_task(_sum, {'a': 10, 'b': item},
                                   on_done=on_done,
                                   task_id='sum-{}'.format(item))
            print(t.result())  # Will wait for execution!

        # Adding tasks with on_done_kwargs
        for item in range(2):
            processes.add_task(_sum, {'a': 5, 'b': item},
                               on_done=handle_result,
                               on_done_kwargs={'operation': "sum(5, {})".format(item)})

    print("After it all")



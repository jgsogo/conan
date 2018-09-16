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
    os.environ['CONAN_LOGGING_LEVEL'] = '10'
    logger = configure_logger()

    with spawn_processes(3) as processes:
        # Let's sum
        output = {}
        with processes.task_group(output=output) as sums:
            for item in range(10):
                sums.add_task(_sum, {'a': 10, 'b': item},
                              on_done=handle_result,
                              on_done_kwargs={'operation': 'sum(10, {})'.format(item)},
                              task_id='sum-{}'.format(item))
        print("After the context scope:")
        for it, value in output.items():
            print("\t{}: {}".format(it, value))


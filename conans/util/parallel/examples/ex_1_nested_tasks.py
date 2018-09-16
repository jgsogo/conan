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
        raise ValueError("Division equals to 0")


def _nothing(a, b, logger):
    logger.debug("_nothing({}, {})".format(a, b))
    pass


def handle_result(operation, r):
    logger.info("Operation was '{}={}'".format(operation, str(r)))
    return r


if __name__ == '__main__':
    os.environ['CONAN_LOGGING_LEVEL'] = '50'
    logger = configure_logger()

    with spawn_processes(3) as processes:
        # Let's sum
        all_tasks = []
        with processes.task_group(id='SUMS'):
            for item in range(2):
                t = processes.add_task(_sum, {'a': 10, 'b': item},
                                       on_done=handle_result,
                                       on_done_kwargs={'operation': 'sum(10, {})'.format(item)},
                                       task_id='sum-{}'.format(item))
                all_tasks.append(t)

                # Inside sums, make a division
                div_tasks = []
                with processes.task_group(id='DIVS-{}'.format(item)):
                    for it_div in range(2):
                        t = processes.add_task(_div, {'a': item, 'b': it_div},
                                               on_done=handle_result,
                                               on_done_kwargs={'operation': 'div({}, {}'.format(item,
                                                                                                it_div)},
                                               task_id='div-{}-{}'.format(item, it_div))
                        div_tasks.append(t)
                        all_tasks.append(t)
                print("After division scope for item {}".format(item))
                for it in div_tasks:
                    print("\t{}: {}".format(it, it.result()))

            print("All tasks:")
            for it in all_tasks:
                print("\t{}: {}".format(it, it.result()))


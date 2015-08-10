#! /usr/bin/env python
import random
import time
import sys
sys.path.append('..')

from taskit.backend import BackEnd, ADMIN_TASKS
from taskit.log import FileLogger, INFO


def random_wait(number):
    time.sleep(random.random())
    return number * 2


def error_maker():
    assert False, 'Why ever did you call this!?'


class RTimeTermLogger(FileLogger):
    
    """
    A dedicated console-logger with a specialized time display, for logging 
    demonstration purposes.
    """
    
    def __init__(self, allowed=None, children=()):
        FileLogger.__init__(self, sys.stdout, allowed, 0, children)
    
    def _time(self):
        return time.time()


def main():
    log = RTimeTermLogger()
    log(INFO, 'Starting...')
    
    tasks = {'wait-double': random_wait, 'get-error': error_maker}
    tasks.update(ADMIN_TASKS)
    backend = BackEnd(tasks, logger=log)
    backend.main()


if __name__ == '__main__':
    main()

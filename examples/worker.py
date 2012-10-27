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


def main():
    log = FileLogger(sys.stdout)
    log(INFO, 'Starting...')
    
    tasks = ADMIN_TASKS
    tasks.update({'wait-double': random_wait, 'get-error': error_maker})
    backend = BackEnd(tasks, logger=log)
    backend.main()


if __name__ == '__main__':
    main()

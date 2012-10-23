import random
import time
import sys
sys.path.append('..')

from taskit.backend import BackEnd
from taskit.log import FileLogger, INFO


def random_wait(number):
    time.sleep(random.random())
    return number * 2


def main():
    log = FileLogger(sys.stdout)
    log(INFO, 'Starting...')

    backend = BackEnd({'wait-double': random_wait}, logger=log)
    backend.main()


if __name__ == '__main__':
    main()

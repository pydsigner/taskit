import time
import sys
sys.path.append('..')

from taskit.simple import taskit
from taskit.resync import Mediator


mediator = Mediator()


@taskit
def worker(*args):
    time.sleep(1)
    mediator.set_result(args)


def main():
    worker.ignore(5, 6)
    print(mediator.get())


if __name__ == '__main__':
    main()

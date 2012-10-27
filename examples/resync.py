import time
import sys
sys.path.append('..')

from taskit.log import FileLogger, INFO, ERROR
from taskit.simple import taskit
from taskit.resync import Mediator, Resyncer, ResyncWaitTimeout


mediator = Mediator()


@taskit
def worker(*args):
    time.sleep(1)
    mediator.set_result(args)


def error_maker():
    raise ValueError('Why *did* you call this!?')


def main():
    log = FileLogger(sys.stdout)
    
    log(INFO, 'Starting worker(5, 6)')
    worker.ignore(5, 6)
    log(INFO, 'Waiting to get the result')
    log(INFO, mediator.get())
    log(INFO, '------')
    
    log(INFO, 'Starting worker(6, 7)')
    worker.ignore(6, 7)
    log(INFO, 'Waiting a maximum of .5s to get the result. Should raise a '
              'ResyncWaitTimeout exception, which we will catch and display.')
    try:
        mediator.get(.5)
    except ResyncWaitTimeout as e:
        log(ERROR, 'Caught ResyncWaitTimeout: %r!' % e)
    log(INFO, '------')
    
    log(INFO, 'Creating a Resyncer for error_maker(), no args')
    resync = Resyncer(error_maker)
    log(INFO, 'Starting the error_maker() Resyncer')
    resync.start()
    log(INFO, 'Getting the result. Should raise a ValueError, which we will '
              'catch and display...')
    try:
        resync.get()
    except ValueError as e:
        log(ERROR, 'Caught ValueError: %r!' % e)
    log(INFO, '------')
    
    log(INFO, 'Creating a Resyncer for the standard function len(), with one '
              'arg: "Python+TaskIt"')
    resync = Resyncer(len, 'Python+TaskIt')
    log(INFO, 'Starting the len("Python+TaskIt") Resyncer')
    resync.start()
    log(INFO, 'Getting the result')
    log(INFO, resync.get())
    log(INFO, '------')


if __name__ == '__main__':
    main()

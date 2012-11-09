import time
import sys
sys.path.append('..')

from taskit.simple import taskit
from taskit.log import FileLogger, INFO, ERROR


log = FileLogger(sys.stdout)


def cb(res):
    log(INFO, 'Called with %r' % res)


def error_cb(e):
    log(ERROR, 'Got an error callback, with arg of %r' % e)


@taskit
def slow_time(wait):
    time.sleep(wait)
    return time.time()


@taskit
def instant_time():
    return time.time()


@taskit
def error_time():
    raise Exception(time.time())


def main():
    log(INFO, 'Waiting for slow_time(1)')
    log(INFO, 'Got result: %s' % slow_time.work(1))
    
    log(INFO, 'Ignoring instant_time()')
    instant_time.ignore()
    
    log(INFO, 'Ignoring error_time()')
    error_time.ignore()
    
    log(INFO, 'Using default error handling with error_time()')
    error_time.callback(cb, None)
    
    log(INFO, 'Using callback with instant_time()')
    instant_time.callback(cb, error_cb)
    
    log(INFO, 'Using callback with error_time()')
    error_time.callback(cb, error_cb)
    
    # Let everything finish
    time.sleep(.1)


if __name__ == '__main__':
    main()

import time
import sys
sys.path.append('..')

from taskit.frontend import FrontEnd
from taskit.log import FileLogger, INFO, ERROR


# Hide DEBUG (very verbose) and IMPORTANT (shouldn't get any of these :P)
log = FileLogger(sys.stdout, [INFO, ERROR])


def demo_cb(res):
    log(INFO, 'Received result: %s' % res)


def error_cb(e):
    both = e.type, e.args
    log(ERROR, 'Received a BackendProcessingError; type=%r, args=%r' % both)


def main():
    backend = '127.0.0.1'
    frontend = FrontEnd([backend], logger=log)
    
    log(INFO, 'Starting 4 wait-double tasks, with args of 1, 3, 5, and 7.')
    frontend.callback('wait-double', demo_cb, None, 1)
    frontend.callback('wait-double', demo_cb, None, 3)
    frontend.callback('wait-double', demo_cb, None, 5)
    frontend.callback('wait-double', demo_cb, None, 7)
    time.sleep(.1)
    
    tasks = frontend.get_tasks(backend)
    if tasks.isdigit():
        log(INFO, 'Backend is running %s jobs...' % tasks)
    else:
        log(INFO, 'Backend is %s' % tasks)
    
    log(INFO, 'Starting a get-error task')
    frontend.callback('get-error', demo_cb, error_cb)
    
    time.sleep(1)
    log(INFO, 'Stopping backend...')
    frontend.send_stop(backend)


if __name__ == '__main__':
    main()

import time
import sys
sys.path.append('..')

from taskit.frontend import FrontEnd
from taskit.log import FileLogger, INFO


log = FileLogger(sys.stdout)


def demo_cb(res):
    log(INFO, 'Received result: %s' % res)


def main():
    frontend = FrontEnd(['127.0.0.1'], logger=log)
    frontend.callback('wait-double', demo_cb, None, 1)
    frontend.callback('wait-double', demo_cb, None, 3)
    frontend.callback('wait-double', demo_cb, None, 5)
    frontend.callback('wait-double', demo_cb, None, 7)
    time.sleep(4)


if __name__ == '__main__':
    main()

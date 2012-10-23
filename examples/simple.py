import time
import sys
sys.path.append('..')

from taskit.simple import taskit


@taskit
def slow_time(wait):
    time.sleep(wait)
    t = time.time()
    return t


def main():
    print(slow_time.work(1))


if __name__ == '__main__':
    main()

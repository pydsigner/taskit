import time
import sys
sys.path.append('..')

from taskit.backend import BackEnd, ADMIN_TASKS


def add(x, y):
    return x + y
def echo(s):
    return s


tasks = dict(ADMIN_TASKS)
tasks.update(dict(add=add, echo=echo))
backend = BackEnd(tasks)


def main():
    backend.main()


if __name__ == '__main__':
    main()

from __future__ import print_function
import timeit
import sys
sys.path.append('..')

from taskit.frontend import FrontEnd


bigstring = '4' * 3000
num = 10000

backend = (sys.argv[1:] or ['localhost'])[0]
frontend = FrontEnd([backend])


def local_1_sub(x, y):
    return x + y
def local_1():
    local_1_sub(4, 4)

def local_2_sub(s):
    return s
def local_2():
    local_2_sub(bigstring)

def remote_1():
    frontend.work('add', 4, 4)
def remote_2():
    frontend.work('echo', bigstring)


def main():
    print('-- TaskIt Speed Testing (all runs x%s) --' % num)
    print('-- Remote host is %r' % backend)
    print('(control) add, no-delay  -->', timeit.timeit(local_1, number=num))
    print('(remote) add, no-delay   -->', timeit.timeit(remote_1, number=num))
    print('(control) echo, no-delay -->', timeit.timeit(local_2, number=num))
    print('(remote) echo, no-delay  -->', timeit.timeit(remote_2, number=num))
    frontend.send_stop(backend)


if __name__ == '__main__':
    main()

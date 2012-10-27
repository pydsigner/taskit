"""
Resychronize your threads.

This module provides a Mediator() class to allow resynchronization. All that is 
required is access to the Mediator() instance from the thread and the waiter. 

A simple example: 

>>> import time
>>> from taskit.simple import taskit
>>> from taskit.resync import Mediator
>>>
>>> mediator = Mediator()
>>>
>>> @taskit
... def worker(*args):
...     time.sleep(1)
...     mediator.set_result(args)
...
>>> worker.ignore(5, 6)
>>> mediator.get()
(5, 6)

Various tweaks could be used to display the othe features of the mediator 
class, such as changing 

...     mediator.set_result(args)
to
...     mediator.set_error(ValueError(args))

Which would raise ValueError((5, 6)) instead; or changing

>>> mediator.get()
to
>>> mediator.get(.5)

Which, if one typed fast enough, increased the time.sleep(), or put the code 
into a script, would raise 
ResyncWaitTimeout('Could not acquire lock within the time allotted')

Note that though these example explain the basic use and features of 
Mediator(), it truly becomes useful when used in situations where either one is 
working from the outside (e.g. when writing callbacks for asychronous 
libraries) or when one could just call a function rather than threading it, but 
have other things which may be accomplished while the thread is running:

>>> launch_thread(mediator, *args)
>>> do_some_time_consuming_stuff()
>>> res = mediator.get()

Or vice versa (that is, the function has the finished product but needs to send 
out some network signals, close some files, etc.):

>>> def process(mediator, args):
...     if not args[0] == get_magic_code():
...         mediator.set_error(AuthError('Bad authentication key!'))
...         remote.alert('Failed authentication for %s' % args[1])

See also the resync.py example script.
"""

import time

from .threaded import *


__all__ = ['ResyncWaitTimeout', 'Mediator', 'Resyncer']


class ResyncWaitTimeout(error):
    pass


class Mediator(object):
    
    """
    A de-asynchronizer with results and errors.
    """
    
    def __init__(self):
        self._lock = allocate_lock()
        # Do it here, to avoid problems later
        self._lock.acquire()
        
    def _wait(self, timeout):
        """
        Based upon an extract from threading.Condition().wait(). Immediately 
        tries to acquire the lock, and then sleeps for a period of time (going 
        1/2ms..1ms..2ms..4ms..50ms), repeating until the lock is acquired or 
        the timeout limit is reached.
        """
        endtime = time.time() + timeout
        # Initial delay of .5ms
        delay = 0.0005
        while 1:
            if self._lock.acquire(0):
                return
            # Nope, let's see if we have some time left to sleep
            remaining = endtime - time.time()
            if remaining <= 0:
                # Nope, let's break to the error
                break
            # Yes, let's increase the delay up to a maximum of 50ms, and 
            # limited to the remaining time
            delay = min(delay * 2, remaining, .05)
            time.sleep(delay)
        raise ResyncWaitTimeout(
          'Could not acquire lock within the time allotted')
        
    
    def set_result(self, res):
        """
        The worker thread should call this if it was successful. Unlike normal 
        functions, which will return None if execution is allowed to fall off 
        the end, either set_result() or self_error() must be called, or the 
        the get()ing side will hang.
        """
        self.result = (True, res)
        self._lock.release()
    
    def set_error(self, e):
        """
        Rather than allowing unmanaged exceptions to explode, or raising errors 
        within thread, the worker thread should call this function with an 
        error class or instance.
        """
        self.result = (False, e)
        self._lock.release()
    
    def get(self, timeout=None):
        """
        Get a result or raise an error. If `timeout` is not None, this function 
        will wait for only `timeout` seconds before raising ThreadTimeout().
        """
        if timeout is None:
            self._lock.acquire()
        else:
            self._wait(timeout)
        
        res = self.result
        if res[0]:
            return res[1]
        else:
            raise res[1]


class Resyncer(object):
    
    """
    A basic wrapper using Mediator() for standard use. Will resync any standard 
    callable.
    """
    
    def __init__(self, func, *args, **kw):
        """
        The actual call will do func(*args, **kw)
        """
        self.mediator = Mediator()
        self.func = func
        self.args = args
        self.kw = kw
    
    def _wrapper(self):
        """
        Wraps around a few calls which need to be made in the same thread.
        """
        try:
            res = self.func(*self.args, **self.kw)
        except Exception as e:
            self.mediator.set_error(e)
        else:
            self.mediator.set_result(res)
    
    def start(self):
        """
        Start the resync'd function.
        """
        threaded(self._wrapper, ())
    
    def get(self, timeout=None):
        """
        Get the result of the resync'd function. Simply calls Mediator().get().
        """
        return self.mediator.get(timeout)

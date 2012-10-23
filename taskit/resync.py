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
ThreadTimeout('Could not acquire lock within the time allotted')

Note that though these example explain the basic use and features of 
Mediator(), it truly becomes useful when used in situations where either one is 
working from the outside (e.g. when writing callbacks for asychronous 
libraries) or when one could just call a function rather than threading it, but 
have other things which may be accomplished while the thread is running:

>>> launch_thread(mediator, *args)
>>> do_some_time_consuming_stuff()
>>> res = mediator.get()

Or vice vera (that is, the function has the finished product but needs to send 
out some network signals, close some files, etc.):

>>> def process(mediator, args):
...     if not args[0] == get_magic_code():
...         mediator.set_error(AuthError('Bad authentication key!'))
...         remote.alert('Failed authentication for %s' % args[1])

See also the resync.py example script.
"""

import time
try:
    from thread import allocate_lock, error
except ImportError:
    from _thread import allocate_lock, error


__all__ = ['ThreadTimeout', 'Mediator']


class ThreadTimeout(error):
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
        Based upon an extract from threading.Condition().wait()
        """
        endtime = time.time() + timeout
        # Initial delay of .5ms
        delay = 0.0005
        while 1:
            gotit = self._lock.acquire(0)
            if gotit:
                break
            remaining = endtime - time.time()
            if remaining <= 0:
                break
            delay = min(delay * 2, remaining, .05)
            time.sleep(delay)
        raise ThreadTimeout('Could not acquire lock within the time allotted')
        
    
    def set_result(self, res):
        """
        The worker thread should call this if it was successful.
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
        if timeout is None:
            self._lock.acquire()
        else:
            self._wait(timeout)
        
        res = self.result
        if res[0]:
            return res[1]
        else:
            raise res[1]

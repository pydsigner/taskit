"""
The local version of TaskIt is a simple asynchronator, similar to Twisted, but 
much simpler and more Pythonistic and without an event-loop.
"""


from .threaded import *


__all__ = ['null_cb', 'taskit', 'Task']


def null_cb(arg):
    """
    Placeholder callback that does nothing.
    """
    pass


def taskit(func):
    """
    Shortcut for a standard subclass of Task(). Can be used as a decorator.
    """
    class NewTask(Task):
        def work(self, *args, **kw):
            return func(*args, **kw)
    return NewTask()


class Task(object):
    
    """
    This class is not useful by itself, work() must be overrided to do 
    something useful.
    """
    
    def work(self, *args, **kw):
        """
        This method is what is Taskified. Override it. A caller can use this to 
        wait for the response rather than threading it away.
        """
        pass
    
    def _do_cb(self, cb, error_cb, *args, **kw):
        """
        Called internally by callback(). Does cb and error_cb selection.
        """
        try:
            res = self.work(*args, **kw)
        except Exception as e:
            if error_cb is None:
                # Just let it explode into the thread-space
                raise
            elif error_cb:
                error_cb(e)
        else:
            # Success, let's call away!
            cb(res)
    
    def callback(self, cb, error_cb, *args, **kw):
        """
        Threads the task, then runs a callback on success or an error callback
        on fail.
        """
        threaded(self._do_cb, (cb, error_cb) + args, kw)
    
    def ignore(self, *args, **kw):
        """
        Thread it and forget it.
        """
        # We want to silence errors
        self.callback(null_cb, False)

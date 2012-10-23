"""
The local version of TaskIt is a simple asynchronator, similar to Twisted, but 
much simpler and more Pythonistic.
"""


try:
    from thread import start_new_thread as threaded
except ImportError:
    # Probably Python3
    from _thread import start_new_thread as threaded


__all__ = ['Task', 'taskit']


class Task(object):
    def work(self, *args, **kw):
        """
        This method is what is Taskified. Override it. A caller can use this to 
        wait for the response rather than threading it away.
        """
        pass
    
    def _do_cb(self, cb, error_cb, *args, **kw):
        try:
            res = self.work(*args, **kw)
        except Exception as e:
            if error_cb is False:
                # We ignore errors.
                return
            elif error_cb is not None:
                # We report errors.
                return error_cb(e)
            else:
                # We reraise errors.
                raise
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
        threaded(self.work, args, kw)


def taskit(func):
    """
    Shortcut for a standard subclass of Task(). Can be used as a decorator.
    """
    class NewTask(Task):
        def work(self, *args, **kw):
            return func(*args, **kw)
    return NewTask()

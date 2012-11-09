"""
This is the frontend to the distributed version of TaskIt.
"""

import socket

from .threaded import *
from .common import *
from .log import *
from .simple import null_cb


__all__ = ['BackendNotAvailableError', 'BackendProcessingError', 'FrontEnd']


class BackendNotAvailableError(Exception):
    """
    Error raised (without arguments) when no backend is available to handle a 
    task.
    """


class BackendProcessingError(Exception):
    
    """
    Error raised when the backend encounters an error during task handling. Has 
    two attributes (type and args) which are set at initialization.
    """
    
    def __init__(self, type, args):
        """
        type -- The type of the error as seen from the backend (e.g. TypeError 
                or ValueError).
        args -- The args which the error was called with (for instance, 
                ValueError('11', 11) would yield ['11', 11])
        """
        self.type = type
        self.args = args
    
    def __str__(self):
        return str((self.type, self.args))
    
    def __repr__(self):
        return '%s(type=%s, args=%s)' % (self.__class__.__name__, 
                                         self.type, self.args)


class FrontEnd(FirstByteProtocol):
    
    """
    The TaskIt DTPM client. 
    """
    
    def __init__(self, backends=(), default_port=DEFAULT_PORT, 
                 logger=null_logger, codec=JSONCodec):
        """
        backends     -- A list consisting of host strings or (host, port) 
                        pairs. For the portless strings, default_port will be 
                        used as the port. 
        default_port -- The port to use for backends not specifying a port. 
        logger       -- A logger supporting the taskit.log interface. 
        codec        -- A codec to be used in converting messages into strings.
        """
        FirstByteProtocol.__init__(self, logger)
        
        self.default_port = default_port
        self.backends = {}
        self.task_counter = {}
        self.codec = codec
        self.add_backends(*backends)
        self.backend_mutex = allocate_lock()
    
    def _sending_task(self, backend):
        """
        Used internally to safely increment `backend`s task count. Returns the 
        overall count of tasks for `backend`.
        """
        self.backend_mutex.acquire()
        self.backends[backend] += 1
        self.task_counter[backend] += 1
        this_task = self.task_counter[backend]
        self.backend_mutex.release()
        return this_task
    
    def _canceling_task(self, backend):
        """
        Used internally to decrement `backend`s current and total task counts 
        when `backend` could not be reached.
        """
        self.backend_mutex.acquire()
        self.backends[backend] -= 1
        self.task_counter[backend] -= 1
        self.backend_mutex.release()
    
    def _closing_task(self, backend):
        """
        Used internally to safely decrement `backend`s task count.
        """
        self.backend_mutex.acquire()
        self.backends[backend] -= 1
        self.backend_mutex.release()
    
    def _expand_host(self, host):
        """
        Used internally to add the default port to hosts not including 
        portnames.
        """
        if isinstance(host, basestring):
            return (host, self.default_port)
        return tuple(host)
    
    def _sorter(self, backend):
        """
        Sorts backends by the client-side task count.
        """
        return self.backends[backend]
    
    def _do_cb(self, task, cb, error_cb, *args, **kw):
        """
        Called internally by callback(). Does cb and error_cb selection.
        """
        try:
            res = self.work(task, *args, **kw)
        except BackendProcessingError as e:
            if error_cb is None:
                self.log(ERROR, e.__traceback__)
                show_err()
            elif error_cb:
                error_cb(e)
        else:
            # Success, let's call away!
            cb(res)
    
    def _package(self, task, *args, **kw):
        """
        Used internally. Simply wraps the arguments up in a list and encodes 
        the list.
        """
        # Implementation note: it is faster to use a tuple than a list here, 
        # because json does the list-like check like so (json/encoder.py:424):
        #   isinstance(o, (list, tuple))
        # Because of this order, it is actually faster to create a list:
        #   >>> timeit.timeit('L = [1,2,3]\nisinstance(L, (list, tuple))')
        #   0.41077208518981934
        #   >>> timeit.timeit('L = (1,2,3)\nisinstance(L, (list, tuple))')
        #   0.49509215354919434
        # Whereas if it were the other way around, using a tuple would be 
        # faster:
        #   >>> timeit.timeit('L = (1,2,3)\nisinstance(L, (tuple, list))')
        #   0.3031749725341797
        #   >>> timeit.timeit('L = [1,2,3]\nisinstance(L, (tuple, list))')
        #   0.6147568225860596
        return self.codec.encode([task, args, kw])
    
    def _work(self, backend, package, ident='', log=True):
        """
        Centralized task worker code. Used internally, see send_signal() and 
        work() for the external interfaces.
        """
        num = self._sending_task(backend)
        if log:
            self.log(INFO, 'Starting %s backend task #%s (%s)' % 
                           (backend, num, ident))
        try:
            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            conn.connect(backend)
            self.send(conn, package)
            result = self.recv(conn)
            self.log(DEBUG, result)
            result = self.codec.decode(result)
        except Exception as e:
            self._canceling_task(backend)
            raise
        else:
            self._closing_task(backend)
            if log:
                self.log(INFO, 'Finished %s backend task #%s (%s)' % 
                               (backend, num, ident))
        finally:
            conn.close()
        
        if result[0] == 'error':
            # We reraise errors in our own way.
            raise BackendProcessingError(*result[1:])
        else:
            return result[1]
    
    def send_signal(self, backend, signal):
        """
        Sends the `signal` signal to `backend`. Raises ValueError if `backend` 
        is not registered with the client. Returns the result.
        """
        backend = self._expand_host(backend)
        if backend in self.backends:
            try:
                return self._work(backend, self._package(signal), log=False)
            except socket.error:
                raise BackendNotAvailableError
        else:
            raise ValueError('No such backend!')
    
    def send_stop(self, backend):
        """
        Sends the STOP signal to `backend`.
        """
        self.send_signal(backend, STOP)
    
    def send_kill(self, backend):
        """
        Sends the KILL signal to `backend`.
        """
        self.send_signal(backend, KILL)
    
    def get_tasks(self, backend):
        """
        Gets a string of the tasks running on `backend`. This string will 
        either be an integer if the backend is up, or else 'down'.Raises 
        ValueError if `backend` is not registered with the client.
        
        Example:
        
        >>> frontend = FrontEnd(['localhost', '****'])
        >>> frontend.get_tasks('localhost')
        '5'
        >>> frontend.get_tasks('****')
        'down'
        >>> frontend.get_tasks('unregistered')
        Traceback (most recent call last):
        [...]
        ValueError: No such backend!
        """
        try:
            res = self.send_signal(backend, STATUS)
        except BackendNotAvailableError:
            res = 'down'
        return res

    def add_backends(self, *backends):
        """
        See the documentation for __init__() to see an explanation of the 
        *backends argument.
        """
        for backend in backends:
            full = self._expand_host(backend)
            self.backends[full] = 0
            self.task_counter[full] = 0
    
    def work(self, task, *args, **kw):
        """
        Handles pushing out the task and getting the response. Can be called 
        directly to wait for the response.
        
        task -- the server-side identifier for the desired task
        *args and **kw will be passed to the task on the server-side.
        
        Return value is generally the same as on the server-side, so if the 
        server has a task for list() named 'list', calling 
          frontend.work('list', '123456')
        should return
          ['1', '2', '3', '4', '5', '6']
        
        All errors are converted into informational BackendProcessingError()s; 
        for example, following the example above,
          frontend.work('list', 42)
        should raise
          BackendProcessingError('TypeError', ["'int' object is not iterable"])
        Which could then be inspected:
          >>> e.type
          'TypeError'
          >>> e.args
          ["'int' object is not iterable"]
        """
        package = self._package(task, *args, **kw)
        backends = sorted(self.backends, key=self._sorter)
        
        for backend in backends:
            try:
                return self._work(backend, package, task)
            except socket.error:
                # We want to just move onto the next backend if we couldn't 
                # connect to this one
                pass
        # Didn't not get a backend, let the caller know!
        raise BackendNotAvailableError
    
    def callback(self, task, cb, error_cb, *args, **kw):
        """
        Threads the task, then runs a callback on success or an error callback
        on fail.
        
        cb       -- The function to be called with a successful result.
        error_cb -- The function to be called when an error occurs.
        
        For information on `task`, *args, and **kw, see work().
        """
        threaded(self._do_cb, (task, cb, error_cb) + args, kw)
    
    def ignore(self, task, *args, **kw):
        """
        Thread it and forget it.
        
        For information on the arguments to this method, see work().
        """
        # We want to silence errors
        self.callback(task, null_cb, False, *args, **kw)

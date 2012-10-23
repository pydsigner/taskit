"""
This is the frontend to the distributed version of TaskIt.
"""

import socket
try:
    from thread import start_new_thread as threaded
except ImportError:
    # Probably we are just using Python 3; if we actually have no threading, 
    # then this will raise an error.
    from _thread import start_new_thread as threaded

from .common import *
from .log import *


__all__ = ['BackendsNotAvailableError', 'FrontEnd']


class BackendsNotAvailableError(Exception):
    pass
class BackendProcessingError(Exception):
    pass


class FrontEnd(object):
    def __init__(self, backends=[], port=DEFAULT_PORT, logger=null_logger, 
                 codec=JSONCodec):
        self.log = logger
        self.port = port
        self.backends = {}
        self.codec = codec
        self.add_backends(backends)
    
    def _expand_host(self, host):
        if isinstance(host, basestring):
            return (host, self.port)
        return host
    
    def _sorter(self, backend):
        return self.backends[backend]
    
    def _do_cb(self, task, cb, error_cb, *args, **kw):
        res = self.work(task, *args, **kw)
        if res[0] == 'error':
            if error_cb is False:
                # We ignore errors.
                return
            elif error_cb is not None:
                # We report errors.
                return error_cb(res[1:])
            else:
                # We reraise errors in our own way.
                raise BackendProcessingError(res[1:])
        # Success, let's call away!
        cb(res[1])
    
    def _connect(self, host):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(host)
        return sock
    
    def _send_end_msg(self, backend, message):
        if backend in self.backends:
            conn = self._connect(backend)
            conn.send(message)
            conn.close()
            self.backends.pop(backend)
        else:
            raise ValueError('No such backend!')
    
    def stop(self, backend):
        self._send_end_msg(backend, STOP)
    def terminate(self, backend):
        self._send_end_msg(backend, KILL)
    
    def get_jobs(self, backend):
        if backend in self.backends:
            try:
                conn = self._connect(backend)
                conn.send(STATUS)
                res = conn.recv(2048).decode()
                conn.close()
            except socket.error:
                res = 'down'
            return res
        else:
            raise ValueError('No such backend!')

    def add_backends(self, backends=[]):
        for backend in backends:
            self.backends[self._expand_host(backend)] = 0
    
    def work(self, task, *args, **kw):
        """
        Handles pushing out the task and getting the response. Can be called 
        directly to wait for the response.
        """
        package = self.codec.encode([task, args, kw])
        backends = sorted(self.backends, key=self._sorter)
        
        done = False
        for backend in backends:
            self.backends[backend] += 1
            self.log(INFO, 'Starting %s backend task #%s (%s)' % 
                           (backend, self.backends[backend], task))
            try:
                conn = self._connect(backend)
                conn.send(bytes(package, 'utf-8'))
                result = conn.recv(2048)
                done = True
                self.log(INFO, 'Finished %s backend task #%s (%s)' % 
                               (backend, self.backends[backend], task))
            except Exception as e:
                if e.__class__ != socket.error:
                    raise
            finally:
                try:
                    conn.close()
                except:
                    pass
                self.backends[backend] -= 1
            
            if done is True:
                self.log(DEBUG, result)
                return self.codec.decode(result.decode())
        
        raise BackendsNotAvailableError
    
    def callback(self, task, cb, error_cb, *args, **kw):
        """
        Threads the task, then runs a callback on success or an error callback
        on fail.
        """
        threaded(self._do_cb, (task, cb, error_cb) + args, kw)
    
    def ignore(self, task, *args, **kw):
        """
        Thread it and forget it.
        """
        threaded(self.work, (task,) + args, kw)

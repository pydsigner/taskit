"""
This is the backend to the distributed version of TaskIt.
"""

import sys
import time
import socket

from .threaded import *
from .common import *
from .log import *


__all__ = ['build_backend', 'task_stop', 'task_kill', 'task_count', 'BackEnd']

END_RESP = .5


def _is_iter(obj):
    """
    Helper function to check for iterator-ness.
    """
    return hasattr(obj, '__iter__')


def build_backend(tasks, default_host=('127.0.0.1', DEFAULT_PORT), *args, 
                  **kw):
    """
    Most of these args are passed directly to BackEnd(). However, default_host 
    is used a bit differently. It should be a (host, port) pair, and may be 
    overridden with cmdline args:
      file.py localhost
      file.py localhost 54545
    """
    host, port = default_host
    if len(sys.args) > 1:
        host = sys.args[1]
    if len(sys.args) > 2:
        port = sys.args[2]
    
    return BackEnd(tasks, host, port, *args, **kw)


def task_stop(backend):
    """
    A task to stop the backend. Should be supported somehow with the standard 
    name. Password protection may eventually be used here to prevent malicious 
    calls.
    """
    # Threaded, because if it isn't, the server will stop receiving new tasks, 
    # but this method, which waits for all tasks to complete, will never see 
    # this because it is being run in a task which will not complete until all 
    # tasks (including itself!) finish.
    threaded(backend.stop_server, ())


def task_kill(backend):
    """
    A task to terminate the backend. As this can really goof things up, and 
    stopper is quite fine unless some tasks are running too slowly, it need not 
    be included.
    """
    # Threaded, because we want to close our connection to the client before 
    # the server terminates
    threaded(backend.terminate_server, ())


def task_count(backend):
    """
    A task to allow getting the backend's task count. Should be supported.
    """
    # Yes, a string, because that's what the client expects
    return str(backend.task_count)


ADMIN_TASKS = {STOP: (task_stop, True), KILL: (task_kill, True), 
               STATUS: (task_count, True)}


class BackEnd(FirstByteProtocol):
    
    """
    The TaskIt DTPM server. Starts, tracks, and handles tasks.
    """
    
    def __init__(self, tasks, host='127.0.0.1', port=DEFAULT_PORT, 
                 logger=null_logger, codec=JSONCodec, end_resp=END_RESP):
        """
        tasks    -- a dict consisting of task:callable or task:(callable,bool) 
                    items. The boolean, which defaults to False, determines 
                    whether or not the BackEnd() instance will be passed as the 
                    first argument to the callable. Useful for tasks needing 
                    backend.subtask(). 
        host     -- The host to bind to. 
        port     -- The port to bind to. 
        logger   -- A logger supporting the taskit.log interface. 
        codec    -- A codec to be used in converting messages into strings. 
        end_resp -- The time (in seconds) that stop_server() and main() should 
                    use to determine the responsiveness: it is used for socket 
                    timeouts and while:sleep() wait loops.
        """
        FirstByteProtocol.__init__(self)
        
        self.tasks = tasks
        self.host = host
        self.port = port
        self.log = logger
        self.codec = codec
        self.task_count = 0
        # Is this necessary to avoid problems with the task counter getting 
        # corrupted? That is, are self.task_count += 1 and self.task_count -= 1 
        # thread-safe?
        self.task_mutex = allocate_lock()
        
    def add_tasks(self, tasks={}):
        """
        See the documentation for __init__() to see an explanation of the 
        `tasks` argument.
        """
        self.tasks.update(tasks)
    
    def _handler(self, conn):
        """
        Connection handler thread. Takes care of communication with the client 
        and running the proper task or applying a signal.
        """
        incoming = self.recv(conn)
        self.log(DEBUG, incoming)
        try:
            # E.g. ['twister', [7, 'invert'], {'guess_type': True}]
            task, args, kw = self.codec.decode(incoming)
            
            # OK, so we've received the information. Now to use it.
            self.log(INFO, 'Fulfilling task %r' % task)
            self.started_task()
            
            pass_backend = False
            obj = self.tasks[task]
            if _is_iter(obj):
                # (callable, bool)
                obj, pass_backend = obj
            if pass_backend:
                # Have to do this, since args is a list
                args = [self] + args
            
            # Get and package the result
            res = ['success', obj(*args, **kw)]
        except Exception as e:
            self.log(ERROR, 'Error while fullfilling task %r: %r' % (task, e))
            res = ['error', e.__class__.__name__, e.args]
            self.log(ERROR, repr(e))
        else:
            self.log(INFO, 'Finished fulfilling task %r' % task)
            
        finally:
            self.send(conn, self.codec.encode(res))
            self.finished_task()
            conn.close()
    
    def subtask(self, func, *args, **kw):
        """
        Helper function for tasks needing to run subthreads. Takes care of 
        remembering that the subtask is running, and of cleaning up after it.
        Example starting a simple.Task():
          backend.subtask(task.ignore, 1, 'a', verbose=False)
        
        *args and **kw will be propagated to `func`.
        """
        self.started_task()
        try:
            func(*args, **kw)
        finally:
            self.finished_task()
    
    def started_task(self):
        """
        Safely announce that a new task is being started. Used internally; 
        if a task needs to run a subthread, use subtask().
        """
        self.task_mutex.acquire()
        self.task_count += 1
        self.task_mutex.release()
    
    def finished_task(self):
        """
        Announce that a task has been finished. Be sure to do this, even an 
        error is produced in the task as, if you don't, the STOP signal will 
        be completely wrecked. subtask() will take care of this for subthreads 
        started using it.
        """
        self.task_mutex.acquire()
        self.task_count -= 1
        self.task_mutex.release()
    
    def stop_server(self):
        """
        Stop receiving connections, wait for all tasks to end, and then 
        terminate the server.
        """
        self.stop = True
        while self.task_count:
            time.sleep(END_RESP)
        self.terminate = True
    
    def terminate_server(self):
        """
        Do a hard termination of the server. May cause problems if child 
        threads are still running.
        """
        self.terminate = True
    
    def main(self):
        """
        Runs the mainloop. Blocks. Can be halted with over a network, or by 
        with either stop_server() or terminate_server().
        """
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.bind((self.host, self.port))
            self.sock.listen(5)
            self.sock.settimeout(END_RESP)
            
            self.stop = self.terminate = False
            
            while not (self.stop or self.terminate):
                try:
                    conn, addr = self.sock.accept()
                except socket.error:
                    # We have timed out, hurry and get back to accept those 
                    # connections!
                    pass
                else:
                    threaded(self._handler, (conn,))
            
            while not self.terminate:
                time.sleep(END_RESP)
            # We are done, the finally will close the socket.
        finally:
            self.sock.close()

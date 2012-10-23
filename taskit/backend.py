"""
This is the backend to the distributed version of TaskIt.
"""

import sys
import time
import socket
try:
    from thread import start_new_thread as threaded, allocate_lock
except ImportError:
    # Probably Python3
    from _thread import start_new_thread as threaded, allocate_lock

from .common import *
from .log import *


__all__ = ['build_backend', 'BackEnd']

END_RESP = 1


def build_backend(tasks, default_host=('127.0.0.1', DEFAULT_PORT), 
                   *args, **kw):
    
    host, port = default_host
    if len(args) > 1:
        host = args[1]
    if len(args) > 2:
        port = args[2]
    
    return BackEnd(tasks, host, port, *args, **kw)


class BackEnd(object):
    def __init__(self, tasks, host='127.0.0.1', port=DEFAULT_PORT, 
                 logger=null_logger, codec=JSONCodec):
        self.tasks = tasks
        self.host = host
        self.port = port
        self.log = logger
        self.codec = codec
        self.jobs = 0
        # Is this necessary to avoid problems with the job counter getting 
        # corrupted? That is, are self.jobs += 1 and self.jobs -= 1 
        # thread-safe?
        self.job_mutex = allocate_lock()
    
    def _wait_to_term(self):
        while self.jobs:
            time.sleep(END_RESP)
        self.terminate = True
    
    def _handler(self, conn):
        incoming = conn.recv(2048)
        self.log(DEBUG, incoming)
        if incoming == STOP:
            threaded(self._wait_to_term, ())
            self.stop = True
        elif incoming == KILL:
            self.terminate = True
        elif incoming == STATUS:
            conn.send(bytes(str(self.jobs), 'utf-8'))
        else:
            task, args, kw = self.codec.decode(incoming.decode())
            self.log(INFO, 'Fulfilling task (%s)' % task)
            self.started_job()
            try:
                res = ['success', self.tasks[task](*args, **kw)]
            # We need to make sure that we decrement the job count and close 
            # the connection no matter what
            except Exception as e:
                self.log(ERROR, 'Failed to fullfill task (%s)' % task)
                self.finished_job()
                einf = ['error', e.__class__.__name__, str(e)]
                conn.send(bytes(self.codec.encode(einf), 'utf-8'))
                conn.close()
                # This won't wreck the whole server, but we will possibly get 
                # some information in a log or a terminal somewhere
                raise
            else:
                self.log(INFO, 'Finished fulfilling task (%s)' % task)
                self.finished_job()
                conn.send(bytes(self.codec.encode(res), 'utf-8'))
                
        conn.close()
    
    def started_job(self):
        self.job_mutex.acquire()
        self.jobs += 1
        self.job_mutex.release()
    
    def finished_job(self):
        self.job_mutex.acquire()
        self.jobs -= 1
        self.job_mutex.release()
    
    def add_tasks(self, tasks={}):
        self.tasks.update(tasks)
    
    def main(self):
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
                    pass
                else:
                    threaded(self._handler, (conn,))
            
            while not self.terminate:
                time.sleep(END_RESP)
            
            # We are done, the finally will close the socket.
        finally:
            # Must close the socket, no matter what
            self.shutdown()
    
    def shutdown(self):
        try:
            self.sock.close()
        except socket.error:
            # No big deal
            pass

import time
import json
import pickle
import sys

from .log import null_logger, ERROR


__all__ = ['DEFAULT_PORT', 'STOP', 'KILL', 'STATUS', 'bytes', 'basestring', 
           'show_err', 'FirstByteCorruptionError', 'FirstByteProtocol', 
           'JSONCodec', 'PickleCodec']

DEFAULT_PORT = 54543

if bytes is str:
    # Python 2
    def bytes(s, enc):
        return s
    basestring = basestring
else:
    # Python 3
    bytes = bytes
    basestring = str


STOP = '<stop>'
KILL = '<kill>'
STATUS = '<status>'


def show_err():
    sys.excepthook(*sys.exc_info())


class FirstByteCorruptionError(Exception):
    """
    Exception raised when the first byte of a FB LMTP message is not a 0 or 1.
    """


class FirstByteProtocol(object):
    
    """
    A mixin class that has methods for sending and receiving information using 
    the First Byte long message transfer protocol.
    """
    
    first = 4
    
    def __init__(self, logger=null_logger, send_size=2048):
        """
        send_size -- The maximum length of the message pieces created. Will not 
                     be exceeded, but will often not be reached. This value 
                     should not exceed 8192 (the largest power of 2 with a 
                     length of 4)
        """
        self.set_size(send_size)
        self.log = logger
    
    def set_size(self, send_size):
        self.send_size = send_size
        self.data_size = send_size - 1
        self.first_msg = bytes(str(self.send_size).zfill(self.first), 'utf-8')
    
    def recv(self, sock):
        size = int(sock.recv(self.first))
        
        data = ''
        bit = '1'
        while bit == '1':
            raw = sock.recv(size).decode()
            
            bit = raw[0]
            if bit not in ('0', '1'):
                self.log(ERROR, 'First char %r not one of "0" or "1"!' % bit)
                raise FirstByteCorruptionError(
                  'Protocol corruption detected! Check that the other side is ' 
                  'not sending bigger chunks than this side is receiving.')
            
            data += raw[1:]
        
        return data
    
    def send(self, sock, data):
        sock.send(self.first_msg)
        
        data = bytes(data, 'utf-8')
        while data:
            bit = b'0' if len(data) < self.send_size else b'1'
            sock.send(bit + data[:self.data_size])
            data = data[self.data_size:]


class JSONCodec(object):
    
    """
    Standard codec using JSON. Good balance of scope and support.
    """
    
    @staticmethod
    def encode(obj):
        return json.dumps(obj)
    @staticmethod
    def decode(enc):
        return json.loads(enc)


class PickleCodec(object):
    
    """
    Basic codec using pickle (default version) for encoding. Do not use if 
    cross-language support is desired.
    """
    
    @staticmethod
    def encode(obj):
        return pickle.dumps(obj)
    @staticmethod
    def decode(enc):
        return pickle.loads(enc)

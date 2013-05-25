import time
import json
import pickle
import sys

from .log import null_logger, ERROR


__all__ = ['DEFAULT_PORT', 'STOP', 'KILL', 'STATUS', 'bytes', 'basestring', 
           'show_err', 'FirstBytesCorruptionError', 'FirstBytesProtocol', 
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


class FirstBytesCorruptionError(Exception):
    """
    Exception raised when the first byte of a FB LMTP message is not a 0 or 1.
    """


class FirstBytesProtocol(object):
    
    """
    A mixin class that has methods for sending and receiving information using 
    the First Bytes long message transfer protocol.
    """
    
    first = 4
    # '%0<first>x'
    size_insert = '%04x'
    
    def __init__(self, logger=null_logger, data_size=2048):
        """
        data_size -- The maximum length of the data slices created. Will not be 
                     exceeded, but in many cases will not ever be reached. This 
                     value can be any positive "short", but the real-world 
                     network concerns mentioned in the official documentation 
                     for `socket.recv()` apply here -- be kind to the program 
                     that your program is communicating with!
        """
        self.set_size(data_size)
        self.log = logger
    
    def _size_bytes(self, size):
        return bytes(self.size_insert % size, 'utf-8')
    
    def _wire_recv(self, sock, size):
        left = size
        data = ''
        while left:
            chunk = sock.recv(left).decode()
            if not chunk:
                raise FirstBytesCorruptionError(
                  'Socket connection or remote codebase is broken!')
            
            data += chunk
            left -= len(chunk)
        
        return data
    
    def set_size(self, data_size):
        """
        Set the data slice size.
        """
        if len(str(data_size)) > self.first:
            raise ValueError(
              'Send size is too large for message size-field width!')
        
        self.data_size = data_size
    
    def recv(self, sock):
        data = ''
        # Cache the header size for speed
        hsize = self.first + 1
        while 1:
            header = self._wire_recv(sock, hsize)
            bit = header[0]
            if bit not in ('0', '1'):
                self.log(ERROR, 'First char %r not one of "0" or "1"!' % bit)
                raise FirstBytesCorruptionError(
                  'Protocol corruption detected -- '
                  'first char in message was not a 0 or a 1!'
                )
            
            # So, how big a piece do we need to grab?
            size = int(header[1:], 16)
            # Get it.
            data += self._wire_recv(sock, size)
            
            # If nothing else will be sent, then we are finished.
            if bit == '0':
                return data
    
    def send(self, sock, data):        
        # Cache max data size for speed
        ds = self.data_size
        # Also cache the "max data size"-sized-data prefix
        norm = b'1' + self._size_bytes(ds)
        
        data = bytes(data, 'utf-8')
        while data:
            dlen = len(data)
            if dlen < ds:
                pre = b'0' + self._size_bytes(dlen)
            else:
                pre = norm
            
            sock.sendall(pre + data[:ds])
            data = data[ds:]


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

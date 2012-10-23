import time
import json
import pickle


__all__ = ['DEFAULT_PORT', 'STOP', 'KILL', 'STATUS', 'bytes', 'basestring', 
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


STOP = bytes('<stop>', 'utf-8')
KILL = bytes('<kill>', 'utf-8')
STATUS = bytes('<status>', 'utf-8')


class JSONCodec(object):
    @staticmethod
    def encode(obj):
        return json.dumps(obj)
    @staticmethod
    def decode(enc):
        return json.loads(enc)


class PickleCodec(object):
    @staticmethod
    def encode(obj):
        return pickle.dumps(obj)
    @staticmethod
    def decode(enc):
        return pickle.loads(enc)

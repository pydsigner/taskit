import time


__all___ = ['DEBUG', 'INFO', 'ERROR', 'IMPORTANT', 'null_logger', 'OutToLog', 
            'OutToError', 'Splitter', 'FileLogger']

DEBUG, INFO, ERROR, IMPORTANT = 'DEBUG', 'INFO', 'ERROR', 'IMPORTANT'


# Supports the whole interface (__call__(imp, msg), close()), but does 
# absolutely nothing
def null_logger(importance, msg):
    pass
null_logger.close = lambda: None


class OutToLog(object):
    
    """
    Presents a file-like interface to the logging mechanism, e.g. to be hooked 
    up to sys.stdout.
    """
    
    def __init__(self, log, level=INFO):
        self.log = log
        self.level = level
    
    def write(self, s):
        self.log(self.level, s)


class OutToError(OutToLog):
    
    """
    A specifically purposed file-like interface to the logging mechanism, 
    designed to be used with:
    
        sys.stderr = OutToError(logger)
    """
    
    def __init__(self, log):
        OutToLog.__init__(self, log, ERROR)


class Splitter(object):
    
    """
    Channels input into several file objects:
    
    (in)--(Splitter)--(out-0)
                   |
                   +--(out-1)
                  ...
                   +--(out-n)
    
    Supports write(), writelines(), flush(), and close().
    """
    
    def __init__(self, files=[]):
        self.files = files
    
    def close(self):
        for f in self.files:
            f.close()
    
    def flush(self):
        for f in self.files:
            f.flush()
    
    def write(s):
        for f in self.files:
            f.write(s)
    
    def writelines(itr):
        # If it is an exaustive iterable, we don't want to just dump everything 
        # into just one file!
        lines = list(itr)
        for f in self.files:
            f.writelines(lines)


class FileLogger(object):
    def __init__(self, fobj, allowed=[DEBUG, INFO, ERROR, IMPORTANT], flush=5):
        """
        @fobj    -- The file-like object to be written to
        @allowed -- The log message types that will be logged
        @flush   -- How many lines to write before flush()ing if greater than 
                    zero, otherwise the file-object will never be flushed.
        """
        self.fobj = fobj
        self.allowed = allowed
        self.flush = flush
        self.count = 0
    
    def __call__(self, importance, msg):
        if importance in self.allowed:
            self.fobj.write(self._format(importance, msg))
        self.count += 1
        if self.count == self.flush:
            self.fobj.flush()
            self.count = 0
    
    def _time(self):
        return time.strftime('%a %d %B %Y, %H:%M:%S')
    
    def _format(self, level, msg):
        """
        Override this to change the logging format
        """
        return '%s (%s)\t%s\n' % (level, self._time(), msg)
    
    def close(self):
        self.fobj.close()

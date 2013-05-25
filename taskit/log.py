import time
import sys


__all___ = ['DEBUG', 'INFO', 'ERROR', 'IMPORTANT', 'null_logger', 'OutToLog', 
            'OutToError', 'Splitter', 'FileLogger', 'LoggerNode']

DEBUG, INFO, ERROR, IMPORTANT = 'DEBUG', 'INFO', 'ERROR', 'IMPORTANT'


# Supports the whole external interface -- __call__(imp, msg) and close() -- 
# but does absolutely nothing
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
        self.cache = ''
    
    def write(self, s):
        lines = s.split('\n')
        lines[0] = self.cache + lines[0]
        while len(lines) > 1:
            self.log(self.level, lines.pop(0))
        self.cache = lines.pop(0)


class OutToError(OutToLog):
    
    """
    A specifically purposed file-like interface to the logging mechanism, 
    designed to be used with
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
        """
        files -- The files to which the calls should be split.
        """
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
        # If it is an exhaustable iterable, we could end up dumping everything 
        # into just one file! Avoid that here.
        lines = list(itr)
        for f in self.files:
            f.writelines(lines)


class LoggerNode(object):
    
    """
    A logging supervisor. It delegates filtered logging events to its 
    subordinates but does not do any logging itself. See the `FileLogger()` 
    sub-class for a class that does.
    """
    
    def __init__(self, children=(), allowed=None):
        """
        children -- The list of sub-loggers. When an *allowed* log event 
                    occurs, it will be forwarded the child loggers as well. Log 
                    events that are not allowed are simply ignored. This forms 
                    a sort of hierarchy sieve, where log events trickle 
                    downwards with fewer and fewer passing. 
        allowed  -- The log message types that will be logged. If `None`, all 
                    events will be accepted.
        """
        self.children = []
        self.add_children(*children)
        self.allowed = allowed
    
    def __call__(self, importance, msg):
        """
        Log message `' '.join(msg)` with `importance` importance.
        """
        # Quick-cache for speed... really!
        allowed = self.allowed
        # Ignore dis-allowed importances.
        if allowed is not None and importance not in allowed:
            return False
        
        for logger in self.children:
            # .__call__() is much faster for classes, but has bad aesthetics...
            logger(importance, msg)
        
        return True
    
    def add_children(self, *loggers):
        """
        Add loggers as children of this logger.
        """
        self.children.extend(loggers)
    
    def close_children(self):
        """
        Close all child loggers.
        """
        for logger in self.children:
            logger.close()


class FileLogger(LoggerNode):
    
    """
    A logger handler for file-like objects, such as sys.stdout, genuine file 
    objects, or Splitter()s.
    """
    
    def __init__(self, fobj, allowed=None, flush=5, children=()):
        """
        fobj  -- The file-like object to be written to.
        flush -- How many lines to write before flush()ing if greater than 
                 zero, otherwise flush will not be called and the close() 
                 method will have to be used to save data.
        """
        LoggerNode.__init__(self, children, allowed)
        
        self.fobj = fobj
        self.flush = flush
        # Set up the flush counter.
        self.count = 0
    
    def __call__(self, importance, msg):       
        # Let the super-class take care of the children...
        res = LoggerNode.__call__(self, importance, msg)
        
        # If we aren't logging this event... well... then don't!
        if not res:
            return False
       
        # Then take care of our handling.
        self.fobj.write(self._format(importance, msg))
        if self.flush:
            self.count += 1
            if self.count == self.flush:
                self.fobj.flush()
                self.count = 0
        
        return True
    
    def _time(self):
        """
        Override this to change the time formatting in the default `_format()` 
        formatter.
        """
        return time.strftime('%a %d %B %Y, %H:%M:%S')
    
    def _format(self, level, msg):
        """
        Override this to change the logging format.
        """
        return '%s (%s)\t%s\n' % (level, self._time(), msg)
    
    def close(self):
        """
        Close the underlying file. Does not close child loggers; see 
        `close_children()`.
        """
        self.fobj.close()

"""
Cross-Python wrapper around thread/_thread exposing the few items actually 
needed, and aliasing start_new_thread to threaded.
"""

try:
    from thread import allocate_lock, error, start_new_thread as threaded
except ImportError:
    # Probably we are just using Python 3; if we actually have no thread, 
    # then this will raise an error.
    from _thread import allocate_lock, error, start_new_thread as threaded

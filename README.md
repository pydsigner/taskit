TaskIt
======

TaskIt is a light-weight library for task delegation and control. TaskIt has 
several aspects, but these are all extensions of the main idea: that dumping 
off execution, whether to just another thread or to a process running on a 
distant computer, should be simple, low-latency, and controllable.

[TaskIt on Github](http://github.com/pydsigner/taskit)

Core modules
------------

The basic same-process task module, the logging module, and the multi-purpose 
resyncronization module fall into this category, as well as the threaded 
module.

simple.py is just that -- a simple task creator. A task can be run in three 
ways: waiting, callbacks, or ignored.

log.py provides the refreshingly simple logging mechanism for TaskIt, with 
splitters, file-like interfaces, and an interface to file-like objects.

resync.py provides a novel way to get the best of both the synchronous and 
asynchronous worlds, with a simple yet powerful API allowing things such as a 
basic producer-consumer model, handing off the results of a callback to another 
function, and more.

threaded.py centralizes the imports (currently three) from thread/_thread.

Distributed modules
-------------------

These modules are the heart of the distributed task processing model (DTPM). 
This model allows remote errors, server introspection, and remote control 
without obfuscating the transport mechanism. By default, the transport 
mechanism uses standard JSON, but a pickle codec is also available, and writing 
custom codecs is quite simple.

common.py provides common constants, functions, and classes.

backend.py is the backend of the distributed task processing model. It provides 
DTPM server writers with the ability to use almost any function without 
modification, and gives allowances for special cases. 

frontend.py is the frontend to the DTPM. The API is similar to that of 
simple.py, with the allowances of routing all calls through a FrontEnd and 
using string identifiers. It provides it's own job count as well as access to 
the backend's job count. It should be noted that a discrepancy between these 
numbers is generally not a bad sign; client load is not necessarily the same as 
server load. Generally, the server count is more meaningful than the client 
count, but the client uses its own count when distributing tasks to avoid the 
dramatic increase in lag that would result from sorting by the server count.

Daemonizing
-----------

The daemonizing folder includes a /etc/init.d/ bash script, a control Python 
script, and a multiduty port expanding Python module/script. The bash script 
belongs in /etc/init.d/ and should be customized to fit your setup. The control 
script and the port expander must be in the same folder. The control script can 
be used manually, and is also used by the bash script. 
The bash script may eventually be replaced by a Python version thereof, at 
which time the port expander script would be changed into a taskit.util module.

Examples
--------

The examples directory contains example scripts for each feature of TaskIt.
* worker.py is an example for taskit.backend and must be running before main.py
  is run. 
* main.py is an example for taskit.frontend and requires worker.py to be run 
  first.
* resync.py demos every feature of taskit.resync.
* simple.py displays many of the taskit.simple features.

Documentation
-------------

More information and documentation can be found in the doc directory.

--------------------------------------------------------------------------------

Copyright (c) 2012 Daniel Foerster/Dsigner Software <pydsigner@gmail.com>
TaskIt is distributed under the LGPLv3 (or greater), see LICENSE for details.

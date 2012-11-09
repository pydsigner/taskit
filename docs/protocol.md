TaskIt DTPM Implementation
==========================

Brief
-----

This document describes the interface between a TaskIt frontend and a TaskIt 
backend. This document does not investigate the use of Pickle instead of JSON, 
as Pickle is a very specific solution but also a simple switch of codecs.

Overview
--------

The TaskIt DTPM interface is a symmetrical sandwich of four parts: 

**TaskIt --> JSON --> FirstByte --> Sockets --> FirstByte --> JSON --> TaskIt**

At each point in the sandwich above, information is decomposed by the 
communicator until it reaches the socket, where it is transported to the 
communicatee and recomposed into a useful object.

Decomposition: TaskIt
---------------------

Regular results are retrieved and become ['success', result] pairs. Errors are 
caught and become ['error', type, args] groups.

*Example: return 50 --> ['success', 50]*

Decomposition: JSON
-------------------

Already at this point, no knowledge of what is happening exists. All that is 
known is that an object must be translated into a string, which is exactly what 
JSON does.

*Example: ['success', 50] --> '["success", 50]'*

Decomposition: FirstByte
------------------------

This layer was recently added to enable the transfer of long messages. It uses 
a preamble to announce the chunk size, and breaks the message up into articles, 
each prefixed with a 1 if another article follows, or a 0 if this article is 
the last. These articles are at this point chunk size or shorter.

*Example: '["success", 50]' --> send('2048'), send('0["success", 50]')*

Middleman: Sockets
------------------

Standard TCP sockets are then used to get the units of information from the 
communicator to the communicatee. This will take several sends, depending upon 
the number of articles to be sent.

Recomposition: FirstByte
------------------------

Now on the communicatee side, FirstByte gets the the preamble to discover the 
chunk size, and reads the articles as they come in, looking for the 0 prefix. 
It then has the complete message recomposed.

*Example: recv('2048'), recv('0["success", 50]') --> '["success", 50]'*

Recomposition: JSON
-------------------

JSON now takes the string and retranslates it into an object.

*Example: '["success", 50]' --> ['success', 50]*

Recomposition: TaskIt
---------------------

TaskIt now analyzes the the object to see whether it is an error or a success. 
If the object is an error, TaskIt raises a single error, with the sent type and 
args information. If the object is a success, TaskIt returns the result 
included.

*Example: ['success', 50] --> return 50*

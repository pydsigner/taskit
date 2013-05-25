TaskIt DTPM Implementation
==========================

Brief
-----

This document describes the process by which a TaskIt backend returns results 
to a TaskIt client. This document does not investigate the use of Pickle 
instead of JSON, as Pickle is a very specific solution but also a simple switch 
of codecs. Nor does this document discuss the chain of events involved in 
sending the execution request to the backend in the first place; this, however, 
is exactly the same, except that the payload and its handling are different.

Overview
--------

The TaskIt DTPM interface is a symmetrical sandwich of four parts: 
TaskIt, JSON, FirstBytes, and Sockets.

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

Decomposition: FirstBytes
-------------------------

This layer was recently added to enable the transfer of long messages; then it 
was improved to be quite robust. In this protocol, each message is split up 
into articles with a set chunk size. Each article has a 5-byte header. The 
first byte is a 0 or a 1: a zero tells the recipient that this article is the 
last, whilst a 1 announces that another will follow. After this is a 4-byte 
payload-size indicator in hexadecimal. Imediately afterwards comes the payload.
While most messages will probably consist of only one article, this protocol 
ensures that there is no arbitrary limit on message size.

*Example: '["success", 50]' --> send('0000f["success", 50]')*

Middleman: Sockets
------------------

Standard TCP sockets are then used to get the units of information from the 
communicator to the communicatee. This will take several sends, depending upon 
the number of articles to be sent.

Recomposition: FirstBytes
-------------------------

Now on the communicatee side, FirstBytes gets the articles as they come in, 
reading the fixed-size headers first to piece the following payloads back 
together. 

*Example: recv('0000f'), recv('["success", 50]') --> '["success", 50]'*

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

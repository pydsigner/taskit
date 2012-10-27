The Speed of TaskIt
===================

Testing
-------

The directory speed_test contains two scripts: taskit_tester.py (the frontend) 
and taskit_tasks.py (the backend). These scripts should be run on any two 
computers that lag measurements are desired for. For benchmarking purposes, 
simply run the two scripts on the same host. For setup analysis, run the 
backend on the server, and run the frontend with the hostname or IP of the 
server as the only argument. The (remote) time, minus the (control) time, 
divided by 10, equals the lag in milliseconds for each type of call. 

Accompanying these scripts are two that merely profile them: profile_tasks.py 
and profile_tester.py, which import and profile the main() functions from the 
other scripts.

Results
-------

During benchmarking on a PowerEdge T110 II equipped with an Intel Xeon X3430 
CPU, and using the loopback interface associated with 'localhost', lag for the 
'add' task tested at .46ms, and lag for the 'echo' task (which, it should be 
noted, is long enough to require being split up into two send()s) tested at 
.50ms. Testing against a remote server has not yet been accomplished. 

Profiling has shown that, at least for loopback connections, most time is spent 
in actually opening the connection This, of course, was predicted by the 
minimal slowing of the 'echo' task in the testing described above.

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

Because benchmarking scores for 10,000 runs were found to be highly variant, 
the run count was temporarily increased to 100,000. During the benchmarking on 
a server using the loopback interface associated with 'localhost', lag for the 
'add' task tested at .490ms, and lag for the 'echo' task (which, it should be 
noted, is long enough to require being split up into two send()s) tested at 
.571ms. Testing against a remote server has not yet been accomplished. 

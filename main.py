# hello.py
# from mpi4py import MPI
# comm = MPI.COMM_WORLD
# rank = comm.Get_rank()
# size = comm.Get_size()
# print "hello world from process ", rank+1, " of ", size

from mutex import Mutex
from conditionvariable import ConditionVariable
from monitor import Monitor
import time

m = Mutex(1)
cv = ConditionVariable(1)
monitor = Monitor()
if monitor.communicationManager.processId > 0:      # ten proces symuluje czekanie
    monitor.lock(m)
    monitor.wait(cv, m)
    monitor.log("Stopped waiting, going to sleep for 2s")
    time.sleep(2)
    monitor.signal(cv)
    monitor.unlock(m)
else:
    time.sleep(5)
    monitor.lock(m)
    monitor.signal(cv)
    monitor.unlock(m)
print("Finished")
monitor.finalize()

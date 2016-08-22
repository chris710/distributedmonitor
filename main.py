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
monitor = Monitor()         # nowe watki tworzone sa w monitorze
if monitor.communicationManager.processId > 0:      # te procesy symuluja czekanie
    monitor.lock(m)
    monitor.wait(cv, m)
    monitor.log("INFO", "Stopped waiting, going to sleep")
    time.sleep(1)
    monitor.signal(cv)
    monitor.unlock(m)
else:
    time.sleep(2)
    monitor.lock(m)
    monitor.signal(cv)
    monitor.unlock(m)
monitor.finalize()

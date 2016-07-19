from threading import Lock
from threading import Condition

existingMutexes = dict()
mutexListMutex = Lock()


class Mutex:
    def __init__(self, idn):
        if self.get_mutex(idn) is not None:
            raise Exception("Mutex already exists")
        self.id = idn                # mutex id
        self.requesting = False     # mutex waiting for CS
        self.requestClock = 0       # timestamp to reject overdue AGREEs
        self.agreeVector = []       # list of received AGREEs (boolean)
        self.heldUpRequests = []    # AGREEs to be sent after unlock
        self.operationMutex = Lock()    # local mutex for blocking communication loop
        self.localMutex = Lock()        # local mutex for thread safe behavior
        self.previousReturn = None  # most recent RETURN
        self.keepAlive = False      #
        self.criticalSectionCondition = Condition()     # for waiting till all AGREEs are collected
        self.criticalSectionMutex = Lock()

        mutexListMutex.lock()
        existingMutexes[self.id] = self
        mutexListMutex.unlock()

    def get_mutex(self, idn):
        mutexListMutex.lock()
        for key, mutex in existingMutexes.items():
            if key == idn:
                mutexListMutex.unlock()
                return mutex
        mutexListMutex.unlock()
        return None

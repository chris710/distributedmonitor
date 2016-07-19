existingMutexes = dict()
mutexListMutex = Mutex(0)

class Mutex:

    def __init__(self, id):
        if self.getMutex(id) is not None :
            raise Exception("Mutex already exists")
        self.id = id                # mutex id
        self.requesting = False     # mutex waiting for CS
        self.requesClock = 0        # timestamp to reject overdue AGREEs
        self.agreeVector = None     # list of received AGREEs
        self.heldUpRequests         # AGREEs to be sent after unlock
        self.operationMutex
        self.localMutex
        self.previousReturn = None  #
        self.keepAlive = False      #

        mutexListMutex.lock()
        existingMutexes[self.id] = self
        mutexListMutex.unlock()

    def getMutex(self, id):
        mutexListMutex.lock()
        for key, mutex in existingMutexes.items():
            if key == id:
                mutexListMutex.unlock()
                return mutex
        mutexListMutex.unlock()
        return None
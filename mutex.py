from message import Message
from threading import Lock
from threading import Condition

existingMutexes = dict()
mutexListMutex = Lock()


class Mutex:
    def __init__(self, idn):
        if self.get_mutex(idn) is not None:
            raise Exception("Mutex already exists")
        self.id = idn               # mutex id
        self.requesting = False     # mutex waiting for CS
        self.locked = False
        self.requestClock = 0       # timestamp to reject overdue AGREEs
        self.agreeVector = None   # list of received AGREEs (boolean)
        self.heldUpRequests = []    # AGREEs to be sent after unlock
        self.operationMutex = Lock()    # local mutex for blocking communication loop
        self.localMutex = Lock()        # local mutex for thread safe behavior
        self.previousReturn = None  # most recent RETURN msg
        self.keepAlive = False      # no one is requesting
        self.criticalSectionCondition = Condition()     # for waiting till all AGREEs are collected
        self.criticalSectionMutex = Lock()

        mutexListMutex.lock()
        existingMutexes[self.id] = self
        mutexListMutex.unlock()

    @staticmethod
    def get_mutex(idn):
        mutexListMutex.lock()
        for key, mutex in existingMutexes.items():
            if key == idn:
                mutexListMutex.unlock()
                return mutex
        mutexListMutex.unlock()
        return None

    def get_data(self):
        if self.previousReturn is not None and self.previousReturn.hasData:
            return self.previousReturn.data
        return None

    def get_data_size(self):
        if self.previousReturn is not None and self.previousReturn.hasData:
            return self.previousReturn.dataSize
        return 0

    def set_data_for_return(self, data, size):
        if self.previousReturn is not None:
            del self.previousReturn
        m = Message()
        m.type = "DATA"
        m.referenceId = self.id
        m.hasData = True
        m.dataSize = size
        m.data = data
        self.previousReturn = m

    def get_mutexes(self):
        mutexListMutex.lock()
        listOfMutexes = []
        for key, mutex in existingMutexes.items():
            listOfMutexes.append(mutex)
        mutexListMutex.unlock()
        return listOfMutexes

    def agree_vector_true(self):
        if self.agreeVector is not None:
            return False
        # for i in range(0, len(self.agreeVector)):
        for key, boolean in self.agreeVector:      # TODO sprawdz czy zawsze dziala
            if boolean != True:
                return False
        return True


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
        self.previousReturn = None  # most recent RETURN msg
        self.keepAlive = False      # no one is requesting, so after CS bc RETURN rather than AGREE
        self.criticalSectionCondition = Condition()     # for waiting till all AGREEs are collected

        with mutexListMutex:
            existingMutexes[self.id] = self

    @staticmethod
    def get_mutex(idn):
        with mutexListMutex:
            for key, mutex in existingMutexes.items():
                if key == idn:
                    return mutex
        return None

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
        with mutexListMutex:
            listOfMutexes = []
            for key, mutex in existingMutexes.items():
                listOfMutexes.append(mutex)
        return listOfMutexes

    def agree_vector_true(self):
        if self.agreeVector is None:
            return False
        return all(i is True for i in self.agreeVector)


from threading import Lock
from threading import Condition

existingConditionVariables = dict()
conditionListMutex = Lock()


class ConditionVariable:
    def __init__(self, idn):
        if self.get_condition_variable(idn) is not None:
            raise Exception("Condition variable already exists")
        self.id = idn
        self.waiting = False
        self.waitingProcesses = []          # list of processes
        self.operationMutex = Lock()
        self.conditionVariable = Condition()

        conditionListMutex.acquire()
        existingConditionVariables[self.id] = self
        conditionListMutex.release()

    @staticmethod
    def get_condition_variable(idn):
        conditionListMutex.acquire()
        for key, var in existingConditionVariables.items():
            if key == idn:
                conditionListMutex.release()
                return var
        conditionListMutex.release()
        return None

    def get_condition_variables(self):
        conditionListMutex.acquire()
        listOfCV = []
        for key, var in existingConditionVariables.items():
            listOfCV.append(var)
        return listOfCV

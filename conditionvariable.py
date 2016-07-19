from threading import Lock
from threading import Condition

existingConditionVariables = dict()
conditionListMutex = Lock()


class ConditionVariable:
    def __init__(self, id):
        if self.getConditionVariable(id) is not None:
            raise Exception("Condition variable already exists")
        self.id = id
        self.waiting = False
        self.waitingProcesses = []          # list of processes
        self.operationMutex = Lock()
        self.conditionVariable = Condition()

        conditionListMutex.lock()
        existingConditionVariables[self.id] = self
        conditionListMutex.unlock()

    def get_condition_variable(self, id):
        conditionListMutex.lock()
        for key, var in existingConditionVariables.items():
            if key == id:
                conditionListMutex.unlock()
                return var
        conditionListMutex.unlock()
        return None

    def get_condition_variables(self):
        conditionListMutex.lock()
        listOfCV = []
        for key, var in existingConditionVariables.items():
            listOfCV.append(var)
        return listOfCV

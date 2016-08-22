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
        self.conditionVariable = Condition()

        with conditionListMutex:
            existingConditionVariables[self.id] = self

    @staticmethod
    def get_condition_variable(idn):
        with conditionListMutex:
            for key, var in existingConditionVariables.items():
                if key == idn:
                    return var
        return None

    def get_condition_variables(self):
        with conditionListMutex:
            listOfCV = []
            for key, var in existingConditionVariables.items():
                listOfCV.append(var)
            return listOfCV

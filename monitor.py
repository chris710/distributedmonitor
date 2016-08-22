from message import Message
from communicationmanager import CommunicationManager
from mutex import Mutex
from conditionvariable import ConditionVariable
from threading import Thread


class Monitor:
    def __init__(self):
        self.quitMessages = 0
        self.communicationManager = CommunicationManager()
        self.communicationThread = Thread(target=self.communication_loop)
        self.communicationThread.start()
        self.log("INFO", "Monitor initialized. ")

    def log(self, level, text):
        self.communicationManager.log(level, text)

    # konczy dzialanie monitora, oglasza to, laczy watki i czysci
    def finalize(self):
        q = Message()
        q.type = "QUIT"
        self.communicationManager.send_broadcast(q)
        q.recipientId = self.communicationManager.processId
        self.communicationManager.send_message(q)
        self.log("TRACE", "Waiting for communication thread to join parent.")
        self.communicationThread.join()
        self.communicationManager.barrier()
        self.log("TRACE", "Communication thread joined")
        self.communicationManager.close()
        self.log("TRACE", "MPI finalized")
        self.log("INFO", "Monitor finalized")

    def enter_critical_section(self, mux):
        if mux is None:
            return
        mux.operationMutex.acquire()
        if mux.requesting and mux.agree_vector_true():    # conditions to enter CS
            if mux.previousReturn is None:          # first time entering CS
                mux.requesting = False
                mux.agreeVector = [False]*(len(mux.agreeVector))
                mux.criticalSectionCondition.acquire()
                mux.criticalSectionCondition.notify()
                mux.criticalSectionCondition.release()
                mux.operationMutex.release()
                return
            else:
                if mux.previousReturn.type == "RETURN":
                    mux.requesting = False
                    mux.agreeVector = [False]*(len(mux.agreeVector))
                    mux.criticalSectionCondition.acquire()
                    mux.criticalSectionCondition.notify()
                    mux.criticalSectionCondition.release()
                    mux.operationMutex.release()
                    return
        mux.operationMutex.release()

    # try to enter CS
    def lock(self, mux):
        mux.operationMutex.acquire()
        mux.requesting = True       # set mux to wait for CS
        mux.keepAlive = False
        if mux.agreeVector is not None:     # reset agreeVector
            del mux.agreeVector
        mux.agreeVector = [False]*self.communicationManager.processCount      # agree vector init
        for i in range(0, self.communicationManager.processCount):
            mux.agreeVector[i] = (i == self.communicationManager.processId)     # set every entry to false except requesting process
        reqmes = Message()
        reqmes.type = "REQUEST"
        reqmes.referenceId = mux.id
        self.communicationManager.send_broadcast(reqmes)        # send requests to everybody
        mux.requestClock = reqmes.clock
        mux.locked = True
        mux.criticalSectionCondition.acquire()
        mux.operationMutex.release()
        while mux.requesting:
            mux.criticalSectionCondition.wait()
        mux.criticalSectionCondition.release()
        self.log("INFO", "("+str(mux.id)+") locked")

    # leave CS
    def unlock(self, mux):
        mux.operationMutex.acquire()
        if not mux.locked:
            mux.operationMutex.release()
            return
        retmes = Message()
        retmes.type = "RETURN"
        retmes.referenceId = mux.id
        if len(mux.heldUpRequests) == 0:
            mux.keepAlive = True    # respond with RETURN instead of AGREE (after CS)
        for proc in mux.heldUpRequests:
            retmes.recipientId = proc
            self.communicationManager.send_message(retmes)
        del mux.heldUpRequests[:]
        mux.requesting = False
        mux.locked = False
        self.communicationManager.get_communication_mutex().acquire()  # create new agreeVector
        mux.agreeVector = dict()
        for i in range(0, self.communicationManager.processCount):
            mux.agreeVector[i] = (i == self.communicationManager.processId)     # set every entry to false except requesting process
        self.communicationManager.get_communication_mutex().release()
        mux.operationMutex.release()
        self.log("INFO", "("+str(mux.id)+") unlocked and leaving CS")

    def wait(self, cv, mux):
        cv.conditionVariable.acquire()
        cv.waiting = True
        retmes = Message()
        retmes.referenceId = cv.id
        retmes.type = "WAIT"
        self.communicationManager.send_broadcast(retmes)
        self.log("INFO", "("+str(cv.id)+")"+" waiting...")
        while cv.waiting:
            self.unlock(mux)
            cv.conditionVariable.wait()
            cv.conditionVariable.release()
            self.log("INFO", "("+str(cv.id)+") Reaquiring lock...")
            self.lock(mux)
        self.log("INFO", "("+str(cv.id)+") Received signal")
        retmes = Message()
        retmes.referenceId = cv.id
        retmes.type = "WAIT_RETURN"
        self.communicationManager.send_broadcast(retmes)

    def signal_all(self, cv):
        self.log("INFO", "("+str(cv.id)+") signaling to all")
        cv.conditionVariable.acquire()
        sigmes = Message()
        sigmes.referenceId = cv.id
        sigmes.type = "SIGNAL"
        for proc in cv.waitingProcesses:
            sigmes.recipientId = proc
            self.communicationManager.send_message(sigmes)
        cv.conditionVariable.release()

    def signal(self, cv):
        self.log("INFO", "("+str(cv.id)+") signaling")
        cv.conditionVariable.acquire()
        sigmes = Message()
        sigmes.referenceId = cv.id
        sigmes.type = "SIGNAL"
        if len(cv.waitingProcesses) >0:
            sigmes.recipientId = cv.waitingProcesses[0]
            self.communicationManager.send_message(sigmes)
        cv.conditionVariable.release()

    def communication_loop(self):
        while True:
            msg = self.communicationManager.recv_message()      # blocking
            if msg is None:
                break
            if msg.type == "REQUEST":    # requesting CS access
                mux = Mutex.get_mutex(msg.referenceId)
                if mux is not None:
                    mux.operationMutex.acquire()
                    if mux.requesting:        # if REQUEST has earlier time then send AGREE
                        if mux.requestClock < msg.clock:  # add to queue
                            mux.heldUpRequests.append(msg.senderId)
                        else:
                            if mux.requestClock == msg.clock and self.communicationManager.processId < msg.senderId:
                                mux.heldUpRequests.append(msg.senderId)
                            else:
                                agreeReply = Message()
                                agreeReply.referenceId = msg.referenceId
                                agreeReply.recipientId = msg.senderId
                                if mux.keepAlive:
                                    agreeReply.type = "RETURN"
                                    if mux.get_data_size() > 0:
                                        agreeReply.hasData = True
                                else:
                                    agreeReply.type = "AGREE"
                                self.communicationManager.send_message(agreeReply)
                    else:
                        if not mux.locked:
                            agreeReply = Message()
                            agreeReply.referenceId = msg.referenceId
                            agreeReply.recipientId = msg.senderId
                            if mux.keepAlive:
                                agreeReply.type = "RETURN"
                            else:
                                agreeReply.type = "AGREE"
                            self.communicationManager.send_message(agreeReply)
                        else:
                            mux.heldUpRequests.append(msg.senderId)
                    mux.operationMutex.release()
            elif msg.type == "RETURN":  # when leaving CS
                mux = Mutex.get_mutex(msg.referenceId)
                if mux is not None:
                    mux.operationMutex.acquire()
                    mux.agreeVector[msg.senderId] = True
                    mux.keepAlive = False
                    if mux.previousReturn is not None:
                        del mux.previousReturn
                    mux.previousReturn = msg
                    mux.operationMutex.release()
                    self.enter_critical_section(mux)
            elif msg.type == "AGREE":           # process agrees to request for CS
                mux = Mutex.get_mutex(msg.referenceId)
                mux.operationMutex.acquire()
                if mux is not None and mux.requesting:
                    mux.agreeVector[msg.senderId] = True       # sender agreed
                    mux.keepAlive = False                      # sb tries to acquire CS
                    mux.operationMutex.release()
                    self.enter_critical_section(mux)       # try to enter CS
                else:
                    mux.operationMutex.release()
            elif msg.type == "WAIT":        # process is waiting
                cv = ConditionVariable.get_condition_variable(msg.referenceId)
                cv.conditionVariable.acquire()
                cv.waitingProcesses.append(msg.senderId)
                cv.conditionVariable.release()
            elif msg.type == "WAIT_RETURN":     # process is not waiting anymore
                cv = ConditionVariable.get_condition_variable(msg.referenceId)
                cv.conditionVariable.acquire()
                cv.waitingProcesses.remove(msg.senderId)
                cv.conditionVariable.release()
            elif msg.type == "SIGNAL":          # wake up waiting process
                cv = ConditionVariable.get_condition_variable(msg.referenceId)
                cv.conditionVariable.acquire()
                cv.waiting = False
                cv.conditionVariable.notify()
                cv.conditionVariable.release()
            elif msg.type == "QUIT":            # process will no longer communicate
                self.quitMessages += 1
                if self.quitMessages == self.communicationManager.processCount:
                    self.communicationManager.initialized = False
                    return

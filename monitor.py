from message import Message
from communicationmanager import CommunicationManager
from mutex import Mutex
from conditionvariable import ConditionVariable
from threading import Lock
from threading import Thread


class Monitor:
    def __init__(self):
        self.quitMessages = 0
        self.communicationManager = CommunicationManager()
        self.log("TRACE", "Monitor created")
        # self.init(0)
        self.log("TRACE", "Monitor initializing...")
        # self.communicationManager.init
        self.communicationThread = Thread(target=self.communication_loop)
        self.log("TRACE", "Monitor: Communication loop started.")
        self.log("INFO", "Monitor initialized. ")

    def log(self, level, text):
        self.communicationManager.log(level, text)

    # def init(self):

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

    def enter_critical_section(self, mux):
        if mux is None:
            return
        mux.operationMutex.lock()
        if mux.requesting and mux.agreeVectorTrue():    # conditions to enter CS
            if mux.previousReturn is None:          # first time entering CS
                mux.requesting = False
                mux.agreeVector = [False]*(len(mux.agreeVector))
                mux.criticalSectionConditionMutex.lock()
                mux.criticalSectionCondition.notify()
                mux.criticalSectionConditionMutex.unlock()
                mux.operationMutex.unlock()
                return
            else:
                if mux.previousReturn.type == "RETURN":
                    if mux.previousReturn.hasData:  # ask for data from previous process that entered
                        reqdata = Message()
                        reqdata.type = "REQUEST_DATA"
                        reqdata.recipientId = mux.previousReturn.senderId
                        reqdata.referenceID = mux.previousReturn.referenceId
                        self.communicationManager.send_message(reqdata)
                    else:
                        mux.requesting = False
                        mux.agreeVector = [False]*(len(mux.agreeVector))
                        mux.criticalSectionConditionMutex.lock()
                        mux.criticalSectionCondition.notify()
                        mux.criticalSectionConditionMutex.unlock()
                        mux.operationMutex.unlock()
                        return
                if mux.previousReturn.type == "DATA":
                    mux.requesting = False
                    mux.agreeVector = [False]*(len(mux.agreeVector))
                    mux.criticalSectionConditionMutex.lock()
                    mux.criticalSectionCondition.notify()
                    mux.criticalSectionConditionMutex.unlock()
                    mux.operationMutex.unlock()
                    return
        mux.operationMutex.unlock()

    # try to enter CS
    def lock(self, mux):
        mux.localMutex.lock()
        mux.operationMutex.lock()
        mux.requesting = True       # set mux to wait for CS
        mux.keepAlive = False
        if mux.agreeVector is not None:     # reset agreeVector
            del mux.agreeVector
        self.communicationManager.get_communication_mutex().lock()
        mux.agreeVector = dict()
        for i in range(0, self.communicationManager.processCount):
            mux.agreeVector[i] = (i == self.communicationManager.processId)     # set every entry to false except requesting process
        self.communicationManager.get_communication_mutex().unlock()
        reqmes = Message()
        reqmes.type = "REQUEST"
        reqmes.referenceId = mux.id
        self.communicationManager.send_broadcast(reqmes)        # send requests to everybody
        mux.requestClock = reqmes.clock
        mux.locked = True
        mux.criticalSectionConditionMutex.lock()
        mux.operationMutex.unlock()
        while mux.requesting:
            mux.criticalSectionCondition.wait()
        mux.criticalSectionConditionMutex.unlock()
        self.log("INFO", "("+str(mux.id)+") locked")

    # leave CS
    def unlock(self, mux):
        mux.operationMutex.lock()
        if not mux.locked:
            mux.operationMutex.unlock()
            return
        retmes = Message()
        retmes.type = "RETURN"
        retmes.referenceId = mux.id
        retmes.hasData = False
        if mux.previousReturn is not None:
            retmes.hasData = mux.previousReturn.hasData
        if len(mux.heldUpRequests) == 0:
            mux.keepAlive = True    # respond with RETURN instead of AGREE (after CS)
        for proc in mux.heldUpRequests:
            retmes.recipientId = proc
            self.communicationManager.send_message(retmes)
        del mux.heldUpRequests[:]
        mux.requesting = False
        mux.locked = False
        self.communicationManager.get_communication_mutex().lock()  # create new agreeVector
        mux.agreeVector = dict()
        for i in range(0, self.communicationManager.processCount):
            mux.agreeVector[i] = (i == self.communicationManager.processId)     # set every entry to false except requesting process
        self.communicationManager.get_communication_mutex().unlock()
        mux.operationMutex.unlock()
        self.log("INFO", "("+str(mux.id)+") leaving CS")
        mux.localMutex.unlock()

    def wait(self, cv, mux):
        cv.operationMutex.lock()


    def communication_loop(self):
        while True:
            self.communicationManager.wait_for_message()
            msg = self.communicationManager.recv_message()
            if msg is None:
                break
            if msg.type == "REQUEST":    # requesting CS access
                mux = Mutex.get_mutex(msg.referenceId)
                if mux is not None:
                    mux.operationMutex.lock()
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
                                    if mux.GET_data_size() > 0:
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
                                if mux.getDataSize() > 0:
                                    agreeReply.hasData = True
                                else:
                                    agreeReply.type = "AGREE"
                                self.communicationManager.send_message(agreeReply)
                        else:
                            mux.heldUpRequests.append(msg.senderId)
                    mux.operationMutex.unlock()
            elif msg.type == "RETURN":  # when leaving CS
                mux = Mutex.get_mutex(msg.referenceId)
                if mux is not None:
                    mux.operationMutex.lock()
                    mux.agreeVector[msg.senderId] = True
                    mux.keepAlive = False
                    if mux.previousReturn is not None:
                        del mux.previousReturn
                    mux.previousReturn = msg
                    mux.operationMutex.unlock()
                    self.enter_critical_section(mux)
            elif msg.type == "REQUEST_DATA":    # when entering CS to get data from previous process
                mux = Mutex.get_mutex(msg.referenceId)
                if mux is not None:
                    mux.operationMutex.lock()
                    if mux.previousReturn is not None and mux.previousReturn.type == "DATA":
                        # copy data packet from mux received earlier and relay it
                        dataMessage = Message(mux.previousReturn)
                        dataMessage.recipientId = msg.senderId
                        self.communicationManager.send_message(dataMessage)
                    mux.operationMutex.unlock()
            elif msg.type == "DATA":    # transmitting data
                mux = Mutex.get_mutex(msg.referenceId)
                if mux is not None:
                    mux.operationMutex.lock()
                    mux.previousReturn = msg    # save message with data to mutex
                    msg = None
                    mux.operationMutex.unlock()
                self.enter_critical_section(mux)
            elif msg.type == "AGREE":           # process agrees to request for CS
                mux = Mutex.get_mutex(msg.referenceId)
                mux.operationMutex.lock()
                if mux is not None and mux.requesting:
                    mux.senderVector[msg.senderId] = True       # sender agreed
                    mux.keepAlive = False;
                    mux.operationMutex.unlock()
                    self.enter_critical_section(mux)       # try to enter CS
                else:
                    mux.operationMutex.unlock()
            elif msg.type == "WAIT":        # process is waiting
                cv = ConditionVariable.get_condition_variable(msg.referenceId)
                cv.operationMutex.lock()
                cv.waitingProcesses.append(msg.senderId)
                cv.operationMutex.unlock()
            elif msg.type == "WAIT_RETURN":     # process is not waiting anymore
                cv = ConditionVariable.get_condition_variable(msg.referenceId)
                cv.operationMutex.lock()
                cv.waitingProcesses.remove(msg.senderId)
                cv.operationMutex.unlock()
            elif msg.type == "SIGNAL":          # wake up waiting process
                cv = ConditionVariable.get_condition_variable(msg.referenceId)
                cv.operationMutex.lock()
                cv.waiting = False
                cv.conditionVariable.notify()
                cv.operationMutex.unlock()
            elif msg.type == "QUIT":            # process will no longer communicate
                self.quitMessages += 1
                if self.quitMessages == self.communicationManager.processCount:
                    self.communicationManager.initialized = False
                    return

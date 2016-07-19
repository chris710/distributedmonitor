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
        if mux.requesting and mux.agreeVectorTrue():
            mux.requesting = False

    def communication_loop(self):
        while True:
            self.communicationManager.wait_for_message()
            msg = self.communicationManager.recv_message()
            if msg is None:
                break
            if msg.type == "REQUEST":    # TODO dodaj wyjasnienia
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
            elif msg.type == "RETURN":
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
            elif msg.type == "REQUEST_DATA":
                mux = Mutex.get_mutex(msg.referenceId)
                if mux is not None:
                    mux.operationMutex.lock()
                    if mux.previousReturn is not None and mux.previousReturn.type == "DATA":
                        # copy data packet from mux received earlier and relay it
                        dataMessage = Message(mux.previousReturn)
                        dataMessage.recipientId = msg.senderId
                        self.communicationManager.send_message(dataMessage)
                    mux.operationMutex.unlock()
            elif msg.type == "DATA":
                mux = Mutex.get_mutex(msg.referenceId)
                if mux is not None:
                    mux.operationMutex.lock()
                    mux.previousReturn = msg    # save message with data to mutex
                    msg = None
                    mux.operationMutex.unlock()
                self.enter_critical_section(mux)
            elif msg.type == "AGREE":
                mux = Mutex.get_mutex(msg.referenceId)
                mux.operationMutex.lock()
                if mux is not None and mux.requesting:
                    mux.senderVector[msg.senderId] = True       # sender agreed
                    mux.keepAlive = False;
                    mux.operationMutex.unlock()
                    self.enter_critical_section(mux)       # try to enter CS
                else:
                    mux.operationMutex.unlock()
            elif msg.type == "WAIT":
                cv = ConditionVariable.get_condition_variable(msg.referenceId)
                cv.operationMutex.lock()
                cv.waitingProcesses.append(msg.senderId)
                cv.operationMutex.unlock()
            elif msg.type == "WAIT_RETURN":
                cv = ConditionVariable.get_condition_variable(msg.referenceId)
                cv.operationMutex.lock()
                cv.waitingProcesses.remove(msg.senderId)
                cv.operationMutex.unlock()
            elif msg.type == "SIGNAL":
                cv = ConditionVariable.get_condition_variable(msg.referenceId)
                cv.operationMutex.lock()
                cv.waiting = False
                cv.conditionVariable.notify_one()       # TODO dablczeknij
                cv.operationMutex.unlock()
            elif msg.type == "QUIT":
                self.quitMessages += 1
                if self.quitMessages == self.communicationManager.processCount:
                    self.communicationManager.initialized = False
                    return




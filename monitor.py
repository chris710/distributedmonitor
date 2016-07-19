from message import Message
from communicationmanager import CommunicationManager
from mutex import Mutex
from conditionvariable import ConditionVariable
from threading import Lock
from threading import Thread


class Monitor:
    def __init__(self):
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

    def communication_loop(self):
        while True:
            self.communicationManager.wait_for_message()
            msg = self.communicationManager.recv_message()
            if msg is None:
                break
            if msg.type == "REQUEST":    # TODO dodaj wyjasnienia
                m = Mutex.get_mutex(msg.referenceId)
                if m is not None:
                    m.operationMutex.lock()

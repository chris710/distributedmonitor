from message import Message
from threading import Lock
from mpi4py import MPI
from time import sleep

#communicationMutex = Lock()


class CommunicationManager:
    def __init__(self):
        self.processName = MPI.Get_processor_name()
        self.processId = MPI.COMM_WORLD.Get_rank()
        self.processCount = MPI.COMM_WORLD.Get_size()
        self.initialized = True
        self.communicationMutex = Lock()
        self.clock = 0

    def close(self):
        if self.initialized:
            self.initialized = False
            MPI.COMM_WORLD.Barrier()
            self.log("TRACE", "Last barrier before shutdown.")
            MPI.Finalize()
            self.log("INFO", "Finished")

    def log(self, level, text):
        if level != "TRACE":          # comment this line for detailed logging info
            message = ""
            if self.processName is not None:
                message = "["+str(self.processName)+" "+str(self.processId)+" ; clock = "+str(self.clock)+" "+"] "
            message += text
            print message

    def send_message(self, msg):
        if not self.initialized:
            return
        with self.communicationMutex:
            if msg is not None:
                self.clock += 1
                msg.senderId = self.processId
                msg.clock = self.clock
                self.log("TRACE", "Sending message "+str(msg.type)+" to "+str(msg.recipientId)+
                        ", clock = " + str(msg.clock)+")")
                MPI.COMM_WORLD.isend(msg.get_array(), dest=msg.recipientId, tag=0)

    def send_broadcast(self, msg):
        if not self.initialized and msg is not None:
            return
        with self.communicationMutex:
            self.clock += 1
            msg.clock = self.clock
            msg.senderId = self.processId
            for i in range(0, self.processCount):
                msg.recipientId = i
                if msg.recipientId == self.processId:
                    continue
                self.log("TRACE", "Sending message " + str(msg.type) + " to " + str(msg.recipientId) +
                        ", clock = " + str(msg.clock) + " )")
                MPI.COMM_WORLD.isend(msg.get_array(), dest=msg.recipientId, tag=0)

    # non-blocking receiving
    def wait_for_message(self):
        if not self.initialized:
            return
        #status = MPI.Status()
        MPI.COMM_WORLD.irecv(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG)
        #while not MPI.COMM_WORLD.Iprobe(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG):
            #sleep(0.05)

    def recv_message(self):
        if not self.initialized:
            return
        #self.communicationMutex.acquire()
        #with self.communicationMutex:
            #status = MPI.Status()
            #MPI.COMM_WORLD.Probe(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG, status=status)
        packet = MPI.COMM_WORLD.irecv(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG)
        msg = Message(packet.wait())
        self.clock = max(self.clock, msg.clock+1)
        #self.communicationMutex.release()
        self.log("TRACE", "Received: " + str(msg.type) + " from " + str(msg.senderId) +
                   ", clock = " + str(msg.clock) + " )")
        return msg

    def get_communication_mutex(self):
        return self.communicationMutex

    def barrier(self):
        MPI.COMM_WORLD.Barrier()

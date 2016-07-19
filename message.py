from collections import namedtuple

# declaration of header field names
dataTransferObject = namedtuple("messageHeader", "clock senderId recipientId type referenceId hasData dataSize data")


class Message:
    def __init__(self, msg):
        self.clock = msg.clock
        self.senderId = msg.senderId
        self.recipientId = msg.recipientId
        self.type = msg.type
        self.referenceId = msg.referenceId
        self.hasData = msg.hasData
        self.dataSize = msg.dataSize
        self.data = msg.data

    def get_array(self):
        m = dataTransferObject(clock=self.clock,
                               senderId=self.senderId,
                               recipientId=self.recipientId,
                               type=self.type,
                               referenceId=self.referenceId,
                               hasData=self.hasData,
                               dataSize=self.dataSize,
                               data=self.data)
        return m

    def compare(self, a, b):
        if a.clock == b.clock:
            return a.senderId < b.senderId
        return a.clock < b.clock

    def __gt__(self, other):
        return self.compare(self, other)



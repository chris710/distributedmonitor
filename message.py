from collections import namedtuple

# declaration of header field names
dataTransferObject = namedtuple("messageHeader", "clock senderId recipientId type referenceId hasData dataSize data")


class Message:
    def __init__(self, msg=None):
        self.clock = msg.clock              # zegar logiczny
        self.senderId = msg.senderId        # nadawca
        self.recipientId = msg.recipientId  # adresat
        self.type = msg.type                # rodzaj wiadomosci (START, REQUEST, AGREE, QUIT, RETURN , REQUEST_DATA, DATA)
        self.referenceId = msg.referenceId  # numer odpowiadajacego mutexa
        self.hasData = msg.hasData          # czy zawiera jakies dane w data
        self.dataSize = msg.dataSize        # wielkosc danych
        self.data = msg.data                # dane

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


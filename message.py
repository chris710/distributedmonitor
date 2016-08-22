from collections import namedtuple

# declaration of header field names
dataTransferObject = namedtuple("messageHeader", "clock senderId recipientId type referenceId hasData dataSize data")


class Message:
    def __init__(self, msg=None):
        if msg is None:
            self.clock = 0             # zegar logiczny
            self.senderId = 0       # nadawca
            self.recipientId = 0  # adresat
            self.type = ""              # rodzaj wiadomosci (START, REQUEST, AGREE, QUIT, RETURN , REQUEST_DATA, DATA)
            self.referenceId = 0  # numer odpowiadajacego mutexa
            #self.hasData = False         # czy zawiera jakies dane w data
            #self.dataSize = 0        # wielkosc danych
            #self.data = None
        else:
            self.clock = msg['clock']
            self.senderId = msg['senderId']
            self.recipientId = msg['recipientId']
            self.type = msg['type']
            self.referenceId = msg['referenceId']
            #self.hasData = msg['hasData']
            #self.dataSize = msg['dataSize']
            #self.data = msg['data']

    def get_array(self):
        m = {'clock':self.clock,
                               "senderId":self.senderId,
                               "recipientId":self.recipientId,
                               "type":self.type,
                               "referenceId":self.referenceId}
                               #"hasData":self.hasData,
                               #"dataSize":self.dataSize,
                               #"data":self.data}
        return m

    def compare(self, a, b):
        if a.clock == b.clock:
            return a.senderId < b.senderId
        return a.clock < b.clock

    def __gt__(self, other):
        return self.compare(self, other)


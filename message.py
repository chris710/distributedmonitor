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
            self.hasData = False         # czy zawiera jakies dane w data
            self.dataSize = 0        # wielkosc danych
            self.data = None
        else:
            self.clock = msg.clock or 0             # zegar logiczny
            self.senderId = msg.senderId or 0       # nadawca
            self.recipientId = msg.recipientId or 0  # adresat
            self.type = msg.type or ""              # rodzaj wiadomosci (START, REQUEST, AGREE, QUIT, RETURN , REQUEST_DATA, DATA)
            self.referenceId = msg.referenceId or 0  # numer odpowiadajacego mutexa
            self.hasData = msg.hasData or False         # czy zawiera jakies dane w data
            self.dataSize = msg.dataSize or 0        # wielkosc danych
            self.data = msg.data                # dane

    def get_array(self):
        m = {'clock':self.clock,
                               "senderId":self.senderId,
                               "recipientId":self.recipientId,
                               "type":self.type,
                               "referenceId":self.referenceId,
                               "hasData":self.hasData,
                               "dataSize":self.dataSize,
                               "data":self.data}
        return m

    def compare(self, a, b):
        if a.clock == b.clock:
            return a.senderId < b.senderId
        return a.clock < b.clock

    def __gt__(self, other):
        return self.compare(self, other)


from .DB_common_object import DB_common_object

class Reciever(DB_common_object):
    
    @classmethod
    def send(cls, data):
        return data
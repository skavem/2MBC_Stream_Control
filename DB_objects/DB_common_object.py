from .DB_connection import DB_connection

class DB_common_object(DB_connection):

    @staticmethod
    def check_str_for_restricted_symbols(check_str: str) -> bool:
        restricted_chars = ',.;"\'][<>?\{\}\\~`'
        if any((c in restricted_chars) for c in check_str): return True
        return False

    @classmethod
    def check_str_for_search(cls, check_str: str):
        if not len(check_str.replace(' ', '')):
            return {'error': "А как искать? :("}
        if cls.check_str_for_restricted_symbols(check_str): 
            return {'error': "Использован запрещенный символ"}
        return None

    @classmethod
    def get(cls):
        print(f"get() method called, but there's none")
        return None

    @classmethod
    def send(cls):
        print(f"send() method called, but there's none")
        return None

    @classmethod
    def edit(cls):
        print(f"edit() method called, but there's none")
        return None
        
    @classmethod
    def create(cls):
        print(f"create() method called, but there's none")
        return None
        
    @classmethod
    def delete(cls):
        print(f"delete() method called, but there's none")
        return None
    
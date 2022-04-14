from .DB_common_object import DB_common_object

class Song(DB_common_object):

    @classmethod
    def __get_song(cls, data):
        coup_req = f"\
            SELECT C.id, C.name, C.text \
            FROM Song_Couplet SC \
            LEFT JOIN Couplet C ON SC.couplet_id = C.id \
            WHERE SC.song_id = {data['song_id']} \
            ORDER BY SC.number"
        couplets = cls.exec_req(coup_req).fetchall()

        return {'couplets': couplets}

    @classmethod
    def __search_song(cls, data):
        song_search_str = data['song_search_str'] 
        
        errors = cls.check_str_for_search(song_search_str)
        if not (errors is None):
            return errors
        
        if any((c in '1234567890') for c in song_search_str):
            found_id = cls.exec_req(f'SELECT S.id FROM Song S WHERE S.number = {int(song_search_str)}').fetchall()
        else:
            found_id = cls.exec_req(f'SELECT S.id FROM Song S WHERE S.name_upper LIKE "%{song_search_str.upper()}%"').fetchall()
        if not len(found_id):
            return {'error': "Ничего нет :("}
            
        return {'found_song_id': found_id[0][0]}

    @classmethod
    def get(cls, data):
        if 'song_search_str' in data:
            return cls.__search_song(data)
        else:
            return cls.__get_song(data)
        
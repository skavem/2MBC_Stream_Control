from .DB_common_object import DB_common_object

class Chapter(DB_common_object):
    
    @classmethod
    def get(cls, data):
        nov_req = f"\
            SELECT COUNT(v.id) FROM Verse v \
            WHERE v.chapter_of = (\
            SELECT c.id FROM Chapter c WHERE c.book_of = '{data['book_id']}' \
            AND c.number = {data['ch_id']})"
        number_of_verses = cls.exec_req(nov_req).fetchall()[0][0]

        ver_req = f"\
            SELECT v.number, v.text FROM Verse v \
            WHERE v.chapter_of = (\
            SELECT c.id FROM Chapter c WHERE c.book_of = '{data['book_id']}' \
            AND c.number = {data['ch_id']})"
        verses = dict(cls.exec_req(ver_req).fetchall())

        return {'number_of_verses': number_of_verses, 'verses': verses}
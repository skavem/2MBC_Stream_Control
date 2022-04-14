from .DB_common_object import DB_common_object

class Book(DB_common_object):

    @classmethod
    def get(cls, data):
        request = f"\
            SELECT COUNT(c.id) \
            FROM Chapter c \
            WHERE c.book_of = '{data['book_id']}'"
        number_of_chapters = cls.exec_req(request).fetchall()[0][0]

        return {'number_of_chapters': number_of_chapters}

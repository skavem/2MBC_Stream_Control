import sqlite3


class DB_connection:
    con = sqlite3.connect('local-remaster.db')
    cur = con.cursor()

    Books = dict(cur.execute('SELECT b.abbrev, b.full_name FROM Book b;').fetchall())
    Songs = list(cur.execute('SELECT s.id, s.number, s.name FROM Song s ORDER BY s.number;').fetchall())

    @classmethod
    def get_cur(cls) -> sqlite3.Cursor:
        return cls.cur

    @classmethod
    def get_books(cls):
        return cls.Books
    
    @classmethod
    def get_songs(cls):
        return cls.Songs

    @classmethod
    def exec_req(cls, req):
        return cls.cur.execute(req)
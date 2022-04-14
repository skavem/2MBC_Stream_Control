from .DB_common_object import DB_common_object

class Couplet(DB_common_object):

    @classmethod
    def __edit_couplet(cls, data):
        req = f"\
            UPDATE Couplet \
            SET text = \"{data['couplet_text']}\", name = \"{data['couplet_name']}\" \
            WHERE id = {data['couplet_id']}"
        cls.exec_req(req)

    @classmethod
    def __new_couplet(cls, data):
        insert_after_number = cls.exec_req(f"\
            SELECT SC.number FROM Song_Couplet SC \
            WHERE SC.couplet_id = {data['couplet_id']}"
        ).fetchone()[0]

        song_id_insert_to = cls.exec_req(f"\
            SELECT SC.song_id FROM Song_Couplet SC \
            WHERE SC.couplet_id = {data['couplet_id']}"
        ).fetchone()[0]

        cls.exec_req(f"\
            UPDATE Song_Couplet SET number = number + 1 \
            WHERE song_id = {song_id_insert_to} AND number > {insert_after_number}"
        )
        cls.exec_req(f"\
            INSERT INTO Couplet (name, text) \
            VALUES (\"{data['couplet_name']}\", \"{data['couplet_text']}\")"
        )

        new_couplet_id = cls.cur.lastrowid
        cls.exec_req(f"\
            INSERT INTO Song_Couplet (song_id, couplet_id, number) \
            VALUES ({song_id_insert_to}, {new_couplet_id}, {insert_after_number + 1})"
        )

    @classmethod
    def __move_up(cls, data):        
        song_id = data['song_id']
        couplet_id = data['couplet_id']
        couplet_number = cls.exec_req(f"\
            SELECT number FROM Song_Couplet SC \
            WHERE couplet_id = {couplet_id} AND song_id = {song_id}"
        ).fetchone()[0]
        if (couplet_number == 0): return

        cls.exec_req(f"\
            UPDATE Song_Couplet SET number = number + 1 \
            WHERE song_id = {song_id} AND number = {couplet_number - 1}"
        )
        cls.exec_req(f"\
            UPDATE Song_Couplet SET number = number - 1 \
            WHERE song_id = {song_id} AND couplet_id = {couplet_id}"
        )

    @classmethod
    def __move_down(cls, data):
        song_id = data['song_id']
        couplet_id = data['couplet_id']

        couplet_number = cls.exec_req(f"\
            SELECT number FROM Song_Couplet SC \
            WHERE couplet_id = {couplet_id} AND song_id = {song_id}"
        ).fetchone()[0]

        couplets_in_song = cls.exec_req(f"\
            SELECT COUNT(id) FROM Song_Couplet WHERE song_id = {song_id}"
        ).fetchone()[0]

        if couplet_number == (couplets_in_song - 1): return

        cls.exec_req(f"\
            UPDATE Song_Couplet \
            SET number = number - 1 \
            WHERE song_id = {song_id} AND number = {couplet_number + 1}")
        cls.exec_req(f"\
            UPDATE Song_Couplet \
            SET number = number + 1 \
            WHERE song_id = {song_id} AND couplet_id = {couplet_id}")


    @classmethod
    def edit(cls, data):
        {
            'edit': cls.__edit_couplet,
            'new': cls.__new_couplet,
            'move_up': cls.__move_up,
            'move_down': cls.__move_down
        }[data['edit_type']](data)
        cls.con.commit()
        return None
        

    @classmethod
    def send(cls, data):
        coup_req = f"\
            SELECT C.text FROM Couplet C \
            LEFT JOIN Song_Couplet SC ON SC.couplet_id = C.id \
            WHERE SC.song_id = {data['song']} AND C.id = \"{data['couplet']}\";"
        text = cls.exec_req(coup_req).fetchone()[0]

        return {'couplet': text}

    @classmethod
    def delete(cls, data):
        couplet_id = data['couplet_id']
        song_id = data['song_id']

        update_couplets_after_number = cls.exec_req(f"\
            SELECT SC.number FROM Song_Couplet SC \
            WHERE SC.couplet_id = {couplet_id}"
        ).fetchone()[0]

        cls.exec_req(f"\
            DELETE FROM Couplet WHERE id = {couplet_id}"
        )

        cls.exec_req(f"\
            UPDATE Song_Couplet SET number = number - 1\
            WHERE song_id = {song_id} AND number > {update_couplets_after_number}"
        )

        cls.exec_req(f"\
            DELETE FROM Song_Couplet WHERE couplet_id = {couplet_id}"
        )
        
        cls.con.commit()
        return None
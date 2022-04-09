import asyncio
import pathlib
import websockets
import json
import sqlite3
import ssl

recievers = set()
transmitters = set()

con = sqlite3.connect('local-remaster.db')
Bible = con.cursor()

Books = dict(Bible.execute('SELECT b.abbrev, b.full_name FROM Book b;').fetchall())
Songs = list(Bible.execute('SELECT s.id, s.number, s.name FROM Song s ORDER BY s.number;').fetchall())

async def message_handler(websocket):    
    def check_str_for_restricted_symbols(check_str: str):
        restricted_chars = ',.;"\'][<>?\{\}\\~`'
        if any((c in restricted_chars) for c in check_str): return True
        return False

    async for parcel in websocket:
        if (parcel == 'Transmitter'):
            transmitters.add(websocket)
            await websocket.send(json.dumps({'books': json.dumps(Books, ensure_ascii=False)}, ensure_ascii=False))
            await websocket.send(json.dumps({'songs': json.dumps(Songs, ensure_ascii=False)}, ensure_ascii=False))
            print('[Info]: Transmitter connected')
            continue
        
        print('[Parcel]: ', parcel)

        parcel = json.loads(parcel)
        if (websocket in transmitters):
            if 'hide_verse' in parcel:
                websockets.broadcast(recievers, json.dumps({'hide_verse': True}, ensure_ascii=False))

            if 'book' in parcel:
                try: 
                    verse = Bible.execute(
                        f"SELECT v.text FROM Verse v \
                            WHERE v.chapter_of = (\
                            SELECT c.id FROM Chapter c \
                            WHERE c.book_of = '{parcel['book']}' AND c.number = {int(parcel['ch'])}) AND v.number = {int(parcel['vr'])};"
                    ).fetchall()[0][0]
                    verse_reference = Bible.execute(f"SELECT b.full_name \
                        FROM Book b \
                        WHERE b.abbrev='{parcel['book']}'").fetchall()[0][0] + f" {parcel['ch']}:{parcel['vr']}"
                    websockets.broadcast(recievers, json.dumps({ 'verse': verse, 'ref': verse_reference }, ensure_ascii=False))
                except Exception as e:
                    await websocket.send(json.dumps({ "error": str(e) }, ensure_ascii=False))
            
            if "get_chapters" in parcel:
                await websocket.send(json.dumps({ "number_of_chapters": 
                Bible.execute(
                    f"SELECT COUNT(c.id) FROM Chapter c WHERE c.book_of = '{parcel['get_chapters']}'").fetchall()[0][0] }, 
                    ensure_ascii=False)
                )

            if "get_verses" in parcel:
                number_of_verses = Bible.execute(
                    f"SELECT COUNT(v.id) FROM Verse v \
                    WHERE v.chapter_of = (\
                    SELECT c.id FROM Chapter c WHERE c.book_of = '{parcel['get_verses']['book']}' \
                    AND c.number = {parcel['get_verses']['ch']})")\
                .fetchall()[0][0]

                verses = dict(Bible.execute(
                    f"SELECT v.number, v.text FROM Verse v \
                    WHERE v.chapter_of = (\
                    SELECT c.id FROM Chapter c WHERE c.book_of = '{parcel['get_verses']['book']}' \
                    AND c.number = {parcel['get_verses']['ch']})")
                .fetchall())

                await websocket.send(
                    json.dumps(
                        {"number_of_verses": number_of_verses,
                        "verses": verses},
                        ensure_ascii=False)
                    )
                
            if "find_verse" in parcel:
                if not len(parcel['find_verse'].replace(' ', '')): continue
                if check_str_for_restricted_symbols(parcel['find_verse']): 
                    await websocket.send(json.dumps({'error': 'Использован запрещенный символ'}, ensure_ascii=False))
                    continue
                    
                try:
                    verses = Bible.execute(f'SELECT v.text, v.number, c.number, b.abbrev \
                        FROM VerseSearch vs \
                        LEFT JOIN Verse v ON vs.id = v.id \
                        INNER JOIN Chapter c ON v.chapter_of = c.id \
                        INNER JOIN Book b ON c.book_of = b.abbrev\
                        WHERE VerseSearch MATCH "{parcel["find_verse"]}" ORDER BY rank LIMIT 25').fetchall()
                    await websocket.send(json.dumps({'search_result': verses}, ensure_ascii=False))
                except Exception as e:
                    await websocket.send(json.dumps({ "error": str(e) }, ensure_ascii=False))
                
            if "get_couplets" in parcel:
                couplets = Bible.execute(f'SELECT C.id, C.name, C.text \
                    FROM Song_Couplet SC \
                    LEFT JOIN Couplet C ON SC.couplet_id = C.id \
                    WHERE SC.song_id = {parcel["get_couplets"]} \
                    ORDER BY SC.number').fetchall()
                await websocket.send(json.dumps({'couplets': couplets}, ensure_ascii=False))

            if "couplet" in parcel:
                text = Bible.execute(f'SELECT C.text FROM Couplet C \
                    LEFT JOIN Song_Couplet SC ON SC.couplet_id = C.id \
                    WHERE SC.song_id = {parcel["song"]} AND C.id = "{parcel["couplet"]}";').fetchone()[0]
                websockets.broadcast(recievers, json.dumps({'couplet': text}, ensure_ascii=False))

            if 'song_search_str' in parcel:
                song_search_str = parcel['song_search_str'] 
                if not len(song_search_str.replace(' ', '')): continue
                if check_str_for_restricted_symbols(song_search_str): 
                    await websocket.send(json.dumps({'error': 'Использован запрещенный символ'}, ensure_ascii=False))
                    continue
                
                if any((c in '1234567890') for c in song_search_str):
                    found_id = Bible.execute(f'SELECT S.id FROM Song S WHERE S.number = {int(song_search_str)}').fetchall()
                else:
                    found_id = Bible.execute(f'SELECT S.id FROM Song S WHERE S.name_upper LIKE "%{song_search_str.upper()}%"').fetchall()
                if not len(found_id):
                    continue

                await websocket.send(json.dumps({'found_song_id': found_id[0][0]}, ensure_ascii=False))

            if 'edit_type' in parcel:
                if parcel['edit_type'] == 'edit':
                    Bible.execute(f'UPDATE Couplet \
                        SET text = "{parcel["couplet_text"]}", name = "{parcel["couplet_name"]}" \
                        WHERE id = {parcel["couplet_id"]}')

                elif parcel['edit_type'] == 'new':
                    insert_after_number = Bible.execute(f'SELECT SC.number FROM Song_Couplet SC \
                        WHERE SC.couplet_id = {parcel["couplet_id"]}').fetchone()[0]
                    song_id_insert_to = Bible.execute(f'SELECT SC.song_id FROM Song_Couplet SC \
                        WHERE SC.couplet_id = {parcel["couplet_id"]}').fetchone()[0]

                    Bible.execute(f'UPDATE Song_Couplet SET number = number + 1 \
                        WHERE song_id = {song_id_insert_to} AND number > {insert_after_number}')
                    Bible.execute(f'INSERT INTO Couplet (name, text) VALUES ("{parcel["couplet_name"]}", "{parcel["couplet_text"]}")')

                    new_couplet_id = Bible.lastrowid
                    Bible.execute(f'INSERT INTO Song_Couplet (song_id, couplet_id, number) \
                        VALUES ({song_id_insert_to}, {new_couplet_id}, {insert_after_number + 1})')

                con.commit()


            if 'remove_couplet_id' in parcel:
                couplet_id_to_delete = parcel['remove_couplet_id']
                update_couplets_after_number = Bible.execute(f'SELECT SC.number FROM Song_Couplet SC \
                        WHERE SC.couplet_id = {parcel["remove_couplet_id"]}').fetchone()[0]
                Bible.execute(f'DELETE FROM Couplet WHERE id = {couplet_id_to_delete}')
                Bible.execute(f'UPDATE Song_Couplet SET number = number - 1\
                    WHERE song_id = {parcel["remove_from_song_id"]} AND number > {update_couplets_after_number}')
                Bible.execute(f'DELETE FROM Song_Couplet WHERE couplet_id = {couplet_id_to_delete}')

                con.commit()

            if 'couplet_move_up' in parcel:
                song_id = parcel['move_from_song_id']
                couplet_number = Bible.execute(f'SELECT number FROM Song_Couplet SC \
                    WHERE couplet_id = {parcel["couplet_move_up"]} AND song_id = {song_id}').fetchone()[0]
                if (couplet_number == 0): continue

                Bible.execute(f'UPDATE Song_Couplet SET number = number + 1 \
                    WHERE song_id = {song_id} AND number = {couplet_number - 1}')
                Bible.execute(f'UPDATE Song_Couplet SET number = number - 1 \
                    WHERE song_id = {song_id} AND couplet_id = {parcel["couplet_move_up"]}')

                con.commit()

            if 'couplet_move_down' in parcel:
                song_id = parcel['move_from_song_id']
                couplet_number = Bible.execute(f'SELECT number FROM Song_Couplet SC \
                    WHERE couplet_id = {parcel["couplet_move_down"]} AND song_id = {song_id}').fetchone()[0]
                couplets_in_song = Bible.execute(f'SELECT COUNT(id) FROM "Song_Couplet" WHERE song_id = 1').fetchone()[0]
                if couplet_number == (couplets_in_song - 1): continue

                Bible.execute(f'UPDATE Song_Couplet SET number = number - 1 \
                    WHERE song_id = {song_id} AND number = {couplet_number + 1}')
                Bible.execute(f'UPDATE Song_Couplet SET number = number + 1 \
                    WHERE song_id = {song_id} AND couplet_id = {parcel["couplet_move_down"]}')

                con.commit()

            if 'hide_song' in parcel:
                websockets.broadcast(recievers, json.dumps({'hide_song': True}, ensure_ascii=False))



async def handler(websocket):
    recievers.add(websocket)
    print('[Info]: Client connected')
    try:
        await message_handler(websocket)
    except websockets.exceptions.ConnectionClosed:
        await websocket.close()
        recievers.remove(websocket)
        try:
            transmitters.remove(websocket)
            print("[Info]: Transmitter disconnected")
        except: 
            print("[Info]: Reciever disconnected")
        return

async def main():
    async with websockets.serve(handler, "192.168.1.100", 8765):
        await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('[Warning]: Exiting because of keyboard interrupt')
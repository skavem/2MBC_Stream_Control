import asyncio
import websockets
import json
import sqlite3

recievers = set()
transmitters = set()

con = sqlite3.connect("local.db")
Bible = con.cursor()
Bible.execute("SELECT b.abbrev, b.full_name FROM Book b;")
Books = dict(Bible.fetchall())

async def message_handler(websocket):
    async for parcel in websocket:
        if (parcel == "Transmitter"):
            transmitters.add(websocket)
            await websocket.send(json.dumps({"books": json.dumps(Books, ensure_ascii=False)}, ensure_ascii=False))
            print("[Info]: Transmitter connected")
            continue
        
        print("[Parcel]: ", parcel)

        parcel = json.loads(parcel)
        if (websocket in transmitters):
            if "hide_all_text" in parcel:
                websockets.broadcast(recievers, json.dumps(parcel, ensure_ascii=False))

            if "book" in parcel:
                try: 
                    verse = Bible.execute(
                        f"SELECT v.text FROM Verse v \
                            WHERE v.chapter_of = (\
                            SELECT c.id FROM Chapter c \
                            WHERE c.book_of = '{parcel['book']}' AND c.number = {int(parcel['ch'])}) AND v.number = {int(parcel['vr'])};"
                    ).fetchall()[0][0]
                    websockets.broadcast(recievers, json.dumps({ "text": verse }, ensure_ascii=False))
                except Exception as e:
                    await websocket.send(json.dumps({ "error": str(e) }, ensure_ascii=False))
            
            if "get_chapters" in parcel:
                await websocket.send(json.dumps({ "number_of_chapters": 
                Bible.execute(f"SELECT COUNT(c.id) FROM Chapter c WHERE c.book_of = '{parcel['get_chapters']}'").fetchall()[0][0] }, ensure_ascii=False))

            if "get_verses" in parcel:
                number_of_verses = Bible.execute(f"SELECT COUNT(v.id) FROM Verse v \
                                                WHERE v.chapter_of = (\
                                                SELECT c.id FROM Chapter c WHERE c.book_of = '{parcel['get_verses']['book']}' \
                                                AND c.number = {parcel['get_verses']['ch']})").fetchall()[0][0]

                verses = dict(Bible.execute(f"SELECT v.number, v.text FROM Verse v \
                                            WHERE v.chapter_of = (\
                                            SELECT c.id FROM Chapter c WHERE c.book_of = '{parcel['get_verses']['book']}' \
                                            AND c.number = {parcel['get_verses']['ch']})").fetchall())

                await websocket.send(json.dumps({
                                        "number_of_verses": number_of_verses,
                                        "verses": verses
                                        }, ensure_ascii=False))

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
    async with websockets.serve(handler, "localhost", 8765):
        await asyncio.Future()

asyncio.run(main())
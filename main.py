import asyncio
import websockets
import json
import sqlite3

recievers = set()
transmitters = set()
with open("ru.json", encoding="utf-8") as f:
    Holy_Bible = json.load(f)

con = sqlite3.connect("local.db")
Bible = con.cursor()
Bible.execute("SELECT b.abbrev, b.full_name FROM Book b;")
Books = dict(Bible.fetchall())

async def message_handler(websocket):
    async for parcel in websocket:
        print(parcel)

        if (parcel == "Transmitter"):
            transmitters.add(websocket)
            await websocket.send(json.dumps({"books": json.dumps(Books, ensure_ascii=False)}, ensure_ascii=False))
            continue

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
                            WHERE c.book_of = '{parcel['book']}' AND c.number = {int(parcel['ch'])}) AND v.number = {int(parcel['vr'])};").fetchall()[0][0]
                    websockets.broadcast(recievers, json.dumps({ "text": verse }, ensure_ascii=False))
                except Exception as e:
                    await websocket.send(json.dumps({ "error": str(e) }, ensure_ascii=False))

async def handler(websocket):
    recievers.add(websocket)
    print('client connected')
    await message_handler(websocket)

async def main():
    async with websockets.serve(handler, "localhost", 8765):
        await asyncio.Future()

asyncio.run(main())
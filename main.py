import asyncio
import websockets
import json

recievers = set()
transmitters = set()
with open("ru.json", encoding="utf-8") as f:
    Holy_Bible = json.load(f)
with open("transitions.json", encoding="utf-8") as f:
    Bible_books = json.load(f)

async def message_handler(websocket):
    async for parcel in websocket:
        print(parcel)

        if (parcel == "Transmitter"):
            transmitters.add(websocket)
            await websocket.send(json.dumps({"books": json.dumps(Bible_books, ensure_ascii=False)}, ensure_ascii=False))
            continue

        parcel = json.loads(parcel)
        if (websocket in transmitters):
            if "hide_all_text" in parcel:
                websockets.broadcast(recievers, json.dumps(parcel, ensure_ascii=False))
            if "book" in parcel:
                verse = Holy_Bible[parcel["book"]][int(parcel["ch"]) - 1][int(parcel["vr"]) - 1]
                websockets.broadcast(recievers, json.dumps({ "text": verse }, ensure_ascii=False))

async def handler(websocket):
    recievers.add(websocket)
    print('client connected')
    await message_handler(websocket)

async def main():
    async with websockets.serve(handler, "localhost", 8765):
        await asyncio.Future()

asyncio.run(main())
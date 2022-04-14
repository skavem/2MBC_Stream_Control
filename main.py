import asyncio
import websockets
import json

from DB_objects.Book import Book
from DB_objects.Chapter import Chapter
from DB_objects.Verse import Verse
from DB_objects.Song import Song
from DB_objects.Couplet import Couplet
from DB_objects.Reciever import Reciever
from DB_objects.DB_connection import DB_connection

recievers = set()
transmitters = set()

Books = DB_connection.Books
Songs = DB_connection.Songs

objects_dict = {
    'book': Book,
    'chapter': Chapter,
    'verse': Verse,
    'song': Song,
    'couplet': Couplet,
    'reciever': Reciever
}

funcs_dict = {
    'get': lambda ob, data: ob.get(data),
    'send': lambda ob, data: ob.send(data),
    'edit': lambda ob, data: ob.edit(data),
    'create': lambda ob, data: ob.create(data),
    'delete': lambda ob, data: ob.delete(data)
}

async def message_handler(websocket):
    # Socket functions
    def message_to_json(message) -> str:
        return json.dumps(message, ensure_ascii=False)
    
    def boradcast_to_all(message):
        websockets.broadcast(recievers, message_to_json(message))

    async def send_to_ws(message):
        await websocket.send(message_to_json(message))
    
    # Parcel functions
    async def auth():
        transmitters.add(websocket)
        await send_to_ws({'books': Books})
        await send_to_ws({'songs': Songs})
        print('[Info]: Transmitter connected')

    parcel_type_dict = {
        'auth': auth,
    }

    async for parcel in websocket:
        print('[Parcel]: ', parcel)

        if (parcel == 'Transmitter'):
            await parcel_type_dict['auth']()
            continue

        parcel = json.loads(parcel)      

        if (websocket not in transmitters): continue

        if parcel['type'] in funcs_dict.keys():
            try:
                ret_val = funcs_dict[parcel['type']](objects_dict[parcel['object']], parcel['data'])
                err_mess = ''
            except KeyError as e:
                err_mess = '[Ошибка]: Не хватает аргумента: '+str(e)
            except Exception as e:
                err_mess = '[Ошибка]: '+ str(e)

            if err_mess:
                print(err_mess)
                await send_to_ws({'error': err_mess})

        if parcel['type'] == 'send':
            boradcast_to_all(ret_val)
            continue
        if ret_val is not None:
            await send_to_ws(ret_val)
            continue



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
    async with websockets.serve(handler, '192.168.1.100', 8765):
        await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('[Warning]: Exiting because of keyboard interrupt')
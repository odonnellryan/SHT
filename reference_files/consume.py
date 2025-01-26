import asyncio
import json

import websockets


async def fetch_tcpdump():
    async with websockets.connect("ws://192.168.1.224:60112", ping_interval=1, ping_timeout=10,
                                  close_timeout=10) as websocket:
        request_data = {
            "command": "getData",
            "id": "asdfj"
        }
        await websocket.send(json.dumps(request_data))
        response = await websocket.recv()
        print("Response from server:", response)


asyncio.run(fetch_tcpdump())

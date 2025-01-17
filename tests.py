import asyncio
import websockets
import json
import time
import sys


async def test():
    uri = "ws://127.0.0.1:8888/"
    try:
        async with websockets.connect(uri) as websocket:
            while True:
                request = json.dumps({"command": "getData", "id": 1})
                await websocket.send(request)
                response = await websocket.recv()
                print(response)
                sys.stdout.flush()
                time.sleep(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.stdout.flush()


asyncio.run(test())

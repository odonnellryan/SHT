import asyncio
import websockets
import json
import time
import sys


async def test():
    # uri = "ws://192.168.1.224:60112/"
    uri = "ws://localhost:60112/"
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

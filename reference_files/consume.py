import asyncio
import re

from data_classes import Roaster
from packet_utils import parse_packet


async def fetch_tcpdump():
    async with websockets.connect("ws://192.168.1.224:50693", ping_interval=1, ping_timeout=10,
                                  close_timeout=10) as websocket:

        control_group = Roaster()
        control_group.plot()

        buffer = b""

        while True:
            # try:
                data = await websocket.recv()
                buffer += data
                packets = re.split(rb"(\d{2}:\d{2}:\d{2}\.\d{6} IP )", buffer)[1:]
                if len(packets) > 1:
                    buffer = packets[-2] + packets[-1]  # Preserve the incomplete last packet
                    for i in range(0, len(packets) - 2, 2):
                        timestamp = packets[i]
                        packet_data = packets[i + 1]
                        full_packet = (timestamp + packet_data).decode("utf-8", errors="ignore")
                        packet = parse_packet(full_packet)
                        control_group.add_data_packet(packet)
                        # print(control_group)
            # except Exception as e:
            #     print(f"Error receiving data: {e}")


asyncio.run(fetch_tcpdump())

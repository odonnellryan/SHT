import datetime
import json
import subprocess
from time import sleep

import dpkt
import tornado.ioloop
import tornado.log
import tornado.web
import tornado.websocket

from data_classes import Roaster
from packet_utils import Packet


def process_reader(cls, pcap_reader):
    for ts, pkt in pcap_reader:

        if not cls.tcpdump_running:
            break

        eth = dpkt.ethernet.Ethernet(pkt)
        if eth.type != dpkt.ethernet.ETH_TYPE_IP:
            continue

        parsed_packet = {
            'timestamp': datetime.datetime.utcfromtimestamp(ts).isoformat(),
            'byte_data': eth.ip.tcp.data,
            'sending_port': eth.ip.tcp.sport,
            'receiving_port': eth.ip.tcp.dport,
        }
        cls.roaster.add_data_packet(Packet(**parsed_packet))
        sleep(0.1)


def monitor_tcpdump(cls):
    while cls.tcpdump_running:
        try:
            cls.tcpdump_process = subprocess.Popen(
                ["tcpdump", "-i", "3", "-w", "-", "-U"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                bufsize=1,
            )
            pcap_reader = dpkt.pcap.Reader(cls.tcpdump_process.stdout)
            process_reader(cls, pcap_reader)

        except Exception as e:
            print(f"TCPDump error: {e}")
        finally:
            if cls.tcpdump_process:
                cls.tcpdump_process.terminate()


def mock_stream_from_file(cls):
    filename = "test_stream.pcap"
    while cls.tcpdump_running:
        try:
            with open(filename, "rb") as f:
                pcap_reader = dpkt.pcap.Reader(f)
                process_reader(cls, pcap_reader)
            print("End of file reached. Restarting...")
        except Exception as e:
            print(f"Error reading file: {e}")


class StreamHandler(tornado.websocket.WebSocketHandler):
    roaster = Roaster()
    tcpdump_process = None
    tcpdump_running = True

    @classmethod
    def start_tcpdump(cls):
        cls.tcpdump_running = True
        tornado.ioloop.IOLoop.current().run_in_executor(None, mock_stream_from_file, cls)

    async def on_message(self, message):
        json_request = json.loads(message)
        if "command" in json_request and json_request["command"] == "getData":
            latest_data = self.roaster.get_latest_for_artisan(json_request["id"])
            json_response = json.dumps({
                "id": json_request.get("id", None),
                "data": latest_data
            })
            await self.write_message(json_response)

    def on_close(self):
        StreamHandler.tcpdump_running = False
        if StreamHandler.tcpdump_process:
            StreamHandler.tcpdump_process.terminate()


def make_app():
    return tornado.web.Application([
        (r"/", StreamHandler),
    ])


def main():
    tornado.log.enable_pretty_logging()
    while True:
        try:
            StreamHandler.start_tcpdump()
            app = make_app()
            port = 8888
            address = "0.0.0.0"  # Change to "127.0.0.1" to listen locally only
            app.listen(port, address)
            tornado.log.app_log.info(f"Tornado server started on {address}:{port}")
            tornado.ioloop.IOLoop.current().start()
        except KeyboardInterrupt:
            tornado.log.app_log.info("Shutdown initiated by user (Ctrl+C).")
            StreamHandler.tcpdump_running = False
            if StreamHandler.tcpdump_process:
                StreamHandler.tcpdump_process.terminate()
            break
        except Exception as e:
            tornado.log.app_log.error(f"Error occurred: {e}. Restarting...")


if __name__ == "__main__":
    main()

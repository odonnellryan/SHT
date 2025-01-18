import datetime
import json
import subprocess

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
            'timestamp': datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).isoformat(),
            'byte_data': eth.ip.tcp.data,
            'sending_port': eth.ip.tcp.sport,
            'receiving_port': eth.ip.tcp.dport,
        }

        cls.roaster.add_data_packet(Packet(**parsed_packet))


def monitor_tcpdump(cls):
    while cls.tcpdump_running:

        try:
            cls.tcpdump_process = subprocess.Popen(
                ["tcpdump", "-i", "3", "-w", "-", "-U"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL
            )
            std_out = cls.tcpdump_process.stdout

            pcap_reader = dpkt.pcap.Reader(std_out)
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

    def check_origin(self, origin):
        return True

    clients = set()

    def open(self):
        StreamHandler.clients.add(self)

    @classmethod
    def start_tcpdump(cls):
        cls.tcpdump_running = True
        tornado.ioloop.IOLoop.current().run_in_executor(None, monitor_tcpdump, cls)

    def _handle_request(self, message):
        json_request = json.loads(message)
        if "command" in json_request and json_request["command"] == "getData":
            latest_data = self.roaster.get_latest_for_artisan()
            resp = {
                "id": json_request.get("id", None),
                "data": latest_data
            }
            self.write_message(resp)

    async def on_message(self, message):
        self._handle_request(message)

    def on_close(self):
        StreamHandler.clients.remove(self)


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
            port = 60112
            address = "0.0.0.0"
            app.listen(port, address)
            tornado.log.app_log.info(f"Tornado server started on {address}:{port}")
            tornado.ioloop.IOLoop.current().start()
        except KeyboardInterrupt:
            tornado.log.app_log.info("Shutdown initiated by user (Ctrl+C).")
            StreamHandler.tcpdump_running = False
            if StreamHandler.tcpdump_process:
                StreamHandler.tcpdump_process.terminate()
            break
        except OSError as e:
            tornado.log.app_log.error(f"OS Error {e}, shutting down. ")
            raise e
        except Exception as e:
            tornado.log.app_log.error(f"Error occurred: {e}. Restarting...")


if __name__ == "__main__":
    main()

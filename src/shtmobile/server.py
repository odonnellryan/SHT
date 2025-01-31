import datetime
import json
import os
import subprocess
import threading
import time

import dpkt
import tornado.ioloop
import tornado.log
import tornado.web
import tornado.websocket

try:
    from shtmobile.data_classes import Roaster
    from shtmobile.packet_utils import Packet
except Exception:
    try:
        from data_classes import Roaster
        from packet_utils import Packet
    except (ImportError, ModuleNotFoundError):
        from src.shtmobile.data_classes import Roaster
        from src.shtmobile.packet_utils import Packet


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
    tcpdump_path = cls.tcpdump_path
    if tcpdump_path is None:
        tcpdump_path = 'tcpdump'
    while cls.tcpdump_running:
        try:
            cls.tcpdump_process = subprocess.Popen(
                ["su", "-c", f"{tcpdump_path}", "-i", "3", "-w", "-"],
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


def write_packets_to_file(file_path, tcpdump_path):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    def monitor_file_size(process, file_path):
        while process.poll() is None:  # Continue while the process is running
            if os.path.getsize(file_path) > 5 * 1024 * 1024:  # 5 MB in bytes
                process.terminate()
                break
            time.sleep(0.1)  # Check file size periodically

    with open(file_path, 'wb') as file:
        tcpdump_process = subprocess.Popen(
            ["su", "-c", f"{tcpdump_path}", "-i", "3", "-w", "-"],
            stdout=file,
            stderr=subprocess.DEVNULL
        )
        threading.Thread(
            target=monitor_file_size,
            args=(tcpdump_process, file_path),
            daemon=True
        ).start()

    return tcpdump_process


def mock_stream_from_file(cls):
    filename = "../../reference_files/tcp.pcap"
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
    tcpdump_path = None

    def check_origin(self, origin):
        return True

    clients = set()

    def open(self):
        StreamHandler.clients.add(self)
        # if not hasattr(self, 'poller') and len(StreamHandler.clients) == 1:
        #     self.start_polling()

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
    #     if not StreamHandler.clients:
    #         self.stop_polling()
    #
    # def start_polling(self):
    #     self.poller = tornado.ioloop.PeriodicCallback(self.poll_condition, 100)
    #     self.poller.start()
    #
    # def stop_polling(self):
    #     if hasattr(self, 'poller'):
    #         self.poller.stop()
    #
    # def poll_condition(self):
    #     if self.roaster.has_dropped_roast():
    #         for client in StreamHandler.clients:
    #             client.write_message({"pushMessage": "drop"})


def make_app():
    return tornado.web.Application([
        (r"/", StreamHandler),
    ])


def main():
    tornado.log.enable_pretty_logging()
    while True:
        try:
            StreamHandler.tcpdump_path = 'tcpdump'
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
            tornado.ioloop.IOLoop.current().stop()
            break
        except OSError as e:
            tornado.log.app_log.error(f"OS Error {e}, shutting down. ")
            raise e
        except Exception as e:
            tornado.log.app_log.error(f"Error occurred: {e}. Restarting...")


if __name__ == "__main__":
    main()

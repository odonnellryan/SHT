"""
StrongHoldTelephone
"""
import datetime
import os
import threading

import toga
import tornado.ioloop
from shtmobile.server import StreamHandler, make_app, write_packets_to_file
from toga.paths import Paths
from toga.style import Pack
from toga.style.pack import COLUMN, ROW


def get_local_folder():
    return Paths().data


class WebServerThread(threading.Thread):

    def __init__(self, *args, **kwargs):
        super(WebServerThread, self).__init__(*args, **kwargs)
        self._stop_event = threading.Event()
        self.server = None
        self.mobile_app = None

    def set_mobile_app(self, mobile_app):
        self.mobile_app = mobile_app

    def start(self):
        try:
            if self.server is not None:
                self.mobile_app.message_box.value += "Server already running.\n"
                return

            StreamHandler.start_tcpdump()
            app = make_app()
            port = int(self.mobile_app.port_input.value)
            address = "0.0.0.0"
            self.server = app.listen(port, address)
            self.mobile_app.message_box.value += f"Tornado server started on {address}:{port}\n"

        except OSError as e:
            self.mobile_app.message_box.value = f"OS Error {e}, shutting down.\n"
            raise e
        except Exception as e:
            self.mobile_app.message_box.value = f"Error occurred: {e}, shutting down...\n"

    def stop(self):
        try:
            StreamHandler.tcpdump_running = False
            if StreamHandler.tcpdump_process:
                StreamHandler.tcpdump_process.terminate()
                StreamHandler.tcpdump_process.wait()

            def stop_tornado():
                ioloop = tornado.ioloop.IOLoop.current()
                ioloop.add_callback(ioloop.stop)

            tornado.ioloop.IOLoop.current().add_timeout(
                datetime.timedelta(seconds=1),
                stop_tornado)

            if self.server is not None:
                self.server.stop()
                self.server = None
            self.mobile_app.message_box.value += "Server shutdown completed.\n"

        except Exception as e:
            self.mobile_app.message_box.value += f"Error during shutdown: {e}\n"
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()


class SHT(toga.App):
    def startup(self):

        self.http_server = None
        self.ioloop = None
        self.tcp_process = None
        self.server_thread = WebServerThread()
        self.server_thread.set_mobile_app(self)

        def start_server(widget):
            self.server_thread.start()

        def stop_server(widget):
            self.server_thread.stop()
            self.server_thread.join()

        def _start_tcp_dump(widget):
            _stop_tcp_dump(widget)
            local_folder = get_local_folder()
            path = os.path.join(local_folder, "tcpdump.pcap")
            try:
                self.message_box.value = f"TCP Dump started in: {path}.\n"
                self.tcp_process = write_packets_to_file(path)
            except Exception as e:
                self.message_box.value = f"Error starting TCP Dump: {e}\n"

        def _stop_tcp_dump(widget):
            if hasattr(self, 'tcp_process') and self.tcp_process is not None:
                self.tcp_process.terminate()
                self.tcp_process = None
                self.message_box.value = "TCP Dump stopped.\n"

        main_box = toga.Box(style=Pack(direction=COLUMN))

        input_box = toga.Box(style=Pack(padding_top=10, direction=ROW))

        self.port_input = toga.TextInput(value="60112", placeholder="Port Number")

        input_box.add(toga.Label('Port:'))
        input_box.add(self.port_input)

        start_button = toga.Button('Start Server', on_press=start_server)
        stop_button = toga.Button('Stop Server', on_press=stop_server)
        start_tcp_dump = toga.Button('Start TCP Dump', on_press=_start_tcp_dump)
        stop_tcp_dump = toga.Button('Stop TCP Dump', on_press=_stop_tcp_dump)

        input_box.add(start_button)
        input_box.add(stop_button)
        input_box.add(start_tcp_dump)
        input_box.add(stop_tcp_dump)

        self.message_box = toga.MultilineTextInput(readonly=True, style=Pack(flex=1, direction=COLUMN))

        main_box.add(input_box)
        main_box.add(input_box)
        main_box.add(self.message_box)

        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = main_box
        self.main_window.show()


def main():
    return SHT()

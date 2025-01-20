"""
StrongHoldTelephone
"""

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW


class SHT(toga.App):
    def startup(self):
        def start_server(widget):
            self.message_box.value = "Server started on port " + self.port_input.value + "\n"

        def stop_server(widget):
            self.message_box.value = "Server stopped.\n"

        main_box = toga.Box()

        self.port_input = toga.TextInput(value="60112", placeholder="Port Number")
        main_box.add(toga.Label('Port:'))
        main_box.add(self.port_input)

        start_button = toga.Button('Start Server', on_press=start_server)
        stop_button = toga.Button('Stop Server', on_press=stop_server)
        main_box.add(start_button)
        main_box.add(stop_button)

        self.message_box = toga.MultilineTextInput(readonly=True)
        main_box.add(self.message_box)

        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = main_box
        self.main_window.show()


def main():
    return SHT()

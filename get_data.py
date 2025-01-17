import re

import pandas as pd


def get_data_received():
    file_path = "c_arrays_received.txt"
    return data_to_dataframe(file_path)


def get_data_sent():
    file_path = "c_arrays_sent.txt"
    return data_to_dataframe(file_path)


def data_to_dataframe(file_path):
    with open(file_path, "r") as f:
        raw_data = f.read()

    packet_matches = re.findall(r"char\s+\w+\[\]\s*=\s*\{([^}]*)\};", raw_data, re.DOTALL)

    packets = []
    for packet in packet_matches:
        byte_values = [int(h, 16) for h in re.findall(r"0x[0-9a-fA-F]{2}", packet)]
        packets.append(byte_values)

    df = pd.DataFrame({"Packet": packets})
    return df

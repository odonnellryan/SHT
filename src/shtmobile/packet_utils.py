import dataclasses

from dpkt import ethernet


@dataclasses.dataclass
class Packet:
    timestamp: str
    receiving_port: int
    sending_port: int
    byte_data: bytes

    @property
    def is_sending(self):
        return self.sending_port < self.receiving_port


def parse_packet(packet) -> Packet:
    timestamp = packet.split(" ")[0]

    ports = packet.split("IP ")[1].split(":")[0]
    sending_port = int(ports.split(".")[1].split(" > ")[0])
    receiving_port = int(ports.split(".")[2])

    hex_data = "\n".join(packet.split("\n")[1:]).replace("\t", "")
    hex_data_cleaned = ''.join(line.split(':', 1)[1].strip() for line in hex_data.split('\n') if ':' in line)
    byte_data = bytes.fromhex(hex_data_cleaned)
    eth = ethernet.Ethernet(byte_data)

    result = Packet(**{
        "timestamp": timestamp,
        "receiving_port": receiving_port,
        "sending_port": sending_port,
        "is_sending": sending_port < receiving_port,
        "byte_data": eth.ip.tcp.data,
    })

    return result

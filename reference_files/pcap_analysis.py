import dpkt

# Input and output file paths
pcap_file = 'tcp.pcap'
output_file = 'output.txt'

with open(pcap_file, 'rb') as f, open(output_file, 'w') as out:
    pcap = dpkt.pcap.Reader(f)
    for ts, buf in pcap:
        eth = dpkt.ethernet.Ethernet(buf)
        if isinstance(eth.data, dpkt.ip.IP):
            ip = eth.data
            if isinstance(ip.data, dpkt.tcp.TCP) or isinstance(ip.data, dpkt.udp.UDP):
                payload = ip.data.data
                if payload:
                    out.write(payload.hex() + '\n')
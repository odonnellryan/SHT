import re


def parse_monitor_data(filtered_lines):
    monitor_data = []

    for data in filtered_lines:
        try:
            bytes_data = [int(byte, 8) for byte in data.split("\\")[1:]]

            if bytes_data[1] == 77:  # Command byte for "Monitor"
                monitor_data.append({
                    "HotAirHeaterLv": bytes_data[2],
                    "HalogenHeaterLv": bytes_data[3],
                    "HotAirBlower": bytes_data[4]
                })
        except Exception:
            continue

    return monitor_data


with open('strace.txt') as o:
    lines = o.readlines()

filtered_lines = []

return_lines = []

for line in lines:
    if '\\t' in line:
        for l in line.split('\\t'):
            if not l:
                continue
            return_lines.append(l.strip())

    elif '\\1\\2\\1' in line:
        for l in line.split('\\1\\2\\1'):
            if not l:
                continue
            return_lines.append(l.strip())
    else:
        return_lines.append(line.strip())

return_lines2 = []

for line in return_lines:
    m = re.match(r"read\((\d+), (.+), (\d+)\)\s+=\s+(-?\d+)", line)
    if not m:
        continue
    fd, data, size_requested, size_returned = m.groups()
    fd = int(fd)

    if fd != 15:
        ln = data.replace('"', '')
        if ln.startswith("0x") or ln == '\\4t' or ln == '\\4u':
            continue
        if '\\4u' in ln:
            for l in ln.split('\\4u'):
                if not l:
                    continue
                return_lines2.append(l.strip())
        elif '\\4t' in ln:
            for l in ln.split('\\4t'):
                if not l:
                    continue
                return_lines2.append(l.strip())
        else:
            return_lines2.append(ln.strip())

for line in return_lines2:
    if line.startswith('\\16\\301') and line:
        filtered_lines.append(line.strip())

filtered_lines = set(filtered_lines)
# Parse monitor data
monitor_data = parse_monitor_data(filtered_lines)

# Print monitor data
for entry in monitor_data:
    print(entry)

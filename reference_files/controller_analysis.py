import get_data
from data_classes import bytes_to_control_value, ControlData

df = get_data.get_data_sent()

filtered_by_third = df[df['Packet'].str[2] == 77]


def conv_bytes_to_data(linked_list):
    if linked_list is None:
        return None
    if len(linked_list) % 2 != 0:
        return None
    result_list = []
    for i in range(len(linked_list) // 2):
        b_arr = [0, 0]
        for j in range(2):
            b_arr[j] += linked_list[i * 2 + j]
        result_list.append(int(bytes(b_arr).hex(), 16))
    return result_list


def get_check_sum_byte(linked_list):
    if linked_list is None:
        raise Exception("getCheckSumByte bytes is Null")
    checksum = sum(linked_list) & 255
    return f"{checksum:02X}".encode()


def conv_int_to_hex_str(i):
    i = min(max(i, 0), 255)
    return str.format("{:02X}", i).encode()


def conv_data_to_bytes(*i_arr):
    if i_arr is None:
        raise Exception("Data is Null")
    b_arr = bytearray(len(i_arr) * 2)
    for i, val in enumerate(i_arr):
        conv_int_to_hex_str_bytes = conv_int_to_hex_str(val)
        for j, byte in enumerate(conv_int_to_hex_str_bytes):
            b_arr[(len(conv_int_to_hex_str_bytes) * i) + j] = byte
    return bytes(b_arr)


def conv_tx_bytes(b, b2, b_arr):
    linked_list = [b2]
    if b_arr:
        linked_list.extend(b_arr)
    check_sum_byte = get_check_sum_byte(linked_list)
    if not check_sum_byte or len(check_sum_byte) != 2:
        return None
    linked_list.extend(check_sum_byte)
    linked_list.insert(0, b)
    linked_list.append(3)
    return bytes(linked_list)


def conv_set_hot_air_bytes(i):
    return conv_tx_bytes(2, 49, conv_data_to_bytes(i))


def conv_set_halogen_bytes(i):
    return conv_tx_bytes(2, 50, conv_data_to_bytes(i))


def conv_set_band_bytes(i):
    return conv_tx_bytes(2, 51, conv_data_to_bytes(i))


def bytes_to_c_array(byte_sequence):
    return ", ".join(f"0x{byte:02X}" for byte in byte_sequence)

hab = conv_set_hot_air_bytes(10)

cd = ControlData()

cd.add_datapoint_from_bytes(bytes([14, 198, 2, 49, 50, 68, 65, 55, 3]))
cd.add_datapoint_from_bytes(bytes([14, 198, 2, 49, 48, 70, 65, 55, 3]))
cd.add_datapoint_from_bytes(bytes([14, 198, 2, 50, 54, 48, 57, 56, 3]))

allowed_sequences = [(14, 190), (14, 191), (14, 192), (14, 193), (14, 194), (14, 195), (14, 196), (14, 197), (14, 198),
                     (14, 199)]

filtered_df = df[df['Packet'].apply(lambda x: tuple(x[:len(allowed_sequences[0])]) in allowed_sequences)]

filtered_df['FirstNBytes'] = filtered_df['Packet'].apply(lambda x: tuple(x[:4]) if len(x) >= 2 else None)

filtered_df = filtered_df.dropna(subset=['FirstNBytes'])

counts = filtered_df['FirstNBytes'].value_counts()

filtered_df['controlSeqs'] = filtered_df['Packet'].apply(lambda x: list(x))

filtered_df['ControlValue'] = filtered_df['controlSeqs'].apply(
    lambda x: bytes_to_control_value(x) if not isinstance(x, Exception) else None)

pass

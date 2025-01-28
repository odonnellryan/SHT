import re

import pandas as pd

from reference_files.controller_analysis import conv_set_band_bytes, conv_bytes_to_data
from src.shtmobile.data_classes import ControlData, bytes_to_control_value

# from src.shtmobile.data_classes import bytes_to_control_value, get_control_sequences

file_path = "sent.txt"

with open(file_path, "r") as f:
    raw_data = f.read()

packet_matches = re.findall(r"char\s+\w+\[\]\s*=\s*\{([^}]*)\};", raw_data, re.DOTALL)

packets = []
for packet in packet_matches:
    byte_values = [int(h, 16) for h in re.findall(r"0x[0-9a-fA-F]{2}", packet)]
    packets.append(byte_values)

df = pd.DataFrame({"Packet": packets})


# write code that for this dataframe we add a new column that is the first three of the "Packet" array
# df['FirstNBytes'] = df['Packet'].apply(lambda x: tuple(x[:3]) if len(x) >= 3 else None)
#
# counts1 = df['FirstNBytes'].value_counts()


def contains_sequence(lst, seq):
    return any(lst[i:i + len(seq)] == list(seq) for i in range(len(lst) - len(seq) + 1))


def not_contain_list_of_sequences(lst, seqs):
    for seq in seqs:
        if contains_sequence(lst, seq):
            return False
    return True


def is_contain_list_of_sequences(lst, seqs):
    for seq in seqs:
        if contains_sequence(lst, seq):
            return True
    return False


check_seqs_neg = (
    (2, 51),
    (2, 49),
    (2, 50),
    (2, 77),
    (20, 2),
    (17, 129),
    (1, 2, 1),
    (20, 2, 90),
    (9, 32),
)

check_controls_all = [(2, 49)]
for item in range(190, 200):
    check_controls_all.append((14, item))

sequence_checkers = (
    (2, 50),
)


def is_drum(lst):
    if lst[0] == 9:
        return True


def find_series_start(lst):
    try:
        if len(lst) >= 3 and lst[0] == 14 and (lst[2] > 51 or (lst[2] == 2 and lst[3] == 49)):
            return True
        return False
    except IndexError:
        return False


def check_starts_with_seq(lst, seqs):
    return any([lst[:len(seq)] == list(seq) for seq in seqs])


# df['OnlySomePackets'] = df["Packet"].apply(
#     lambda x: x if isinstance(x, list) and x[0] not in (17, 20, 4) else None
# )
# df = df.dropna(subset=['OnlySomePackets'])


c = ControlData()

# drop all rows not in this index: .iloc[9370:9400]

def get_control_value(x):
    try:
        cv = c.get_datapoint_and_control_value(x)[0]
    except Exception:
        return None
    if cv and cv[0] and 49 in cv[0]:
        return cv
    return None


def bytes_to_control_value(byte_sequence):
    if byte_sequence[-1] == 3:
        byte_sequence.pop()
    if not byte_sequence or len(byte_sequence) < 6:
        return None
    try:
        core_bytes = byte_sequence[4:6]
    except IndexError:
        return 0
    try:
        return [int(bytes(core_bytes[i:i + 2]).decode(), 16) for i in range(0, len(core_bytes), 2)][0]
    except Exception as e:
        return None


df['ControlValue'] = df['Packet'].apply(
    lambda x: get_control_value(x))

# drop rows where ControlValue is nan:
# df = df.dropna(subset=['ControlValue'])

# counts = df['OnlySomePackets'].value_counts()


test_band_0 = [111, 111] + [h for h in conv_set_band_bytes(0)]
test_band_1 = [111, 111] + [h for h in conv_set_band_bytes(5)]
test_band_2 = [111, 111] + [h for h in conv_set_band_bytes(10)]
test_band_3 = [111, 111] + [h for h in conv_set_band_bytes(15)]
test_band_4 = [111, 111] + [h for h in conv_set_band_bytes(120)]
test_decoded = bytes_to_control_value([14, 198, 2, 51, 55, 56, 65, 50, 3])
pass


# 6842 - 7229

# grouped_packets = [
#     df.iloc[i:i + 100] for i in range(0, len(df), 100)
# ]
#
# unique_groups = [group.drop_duplicates(subset=['Packet']) for group in grouped_packets]

# rejoined_df = pd.concat(unique_groups, ignore_index=True)

# allowed_sequences = [(17, 129, 18), (17, 129, 8), (17, 129, 9), (17, 129, 17)]

# storage (surface) is 9
# exhause is 8
# hot air is 2
# drum is 17

# titles = ["Hot Air", "Exhaust", "Storage", "Drum"]
#
# for i, seq in enumerate(allowed_sequences):
#     rejoined_df[f'{titles[i]}'] = rejoined_df['Packet'].apply(
#         lambda x: x if tuple(x[:len(seq)]) == seq else None
#     )
#
# filtered_column_df = rejoined_df[[f'{titles[i]}' for i in range(len(allowed_sequences))]]
# filtered_column_df = filtered_column_df.dropna(how='all')


# rejoined_df['First_Two_Bytes'] = rejoined_df['Packet'].apply(lambda x: tuple(x[:3]) if len(x) >= 2 else None)
#
# filtered_df = rejoined_df.dropna(subset=['First_Two_Bytes'])
#
# counts = filtered_df['First_Two_Bytes'].value_counts()

# def get_resistance(reading, reference_resistance):
#     """Read the resistance of the RTD and return its value in Ohms."""
#     resistance = reading
#     resistance /= 32768
#     resistance *= reference_resistance
#     return resistance
#
#
# def get_temperature(rtd_nominal, reference_resistance, reading):
#
#     raw_reading = get_resistance(reading, reference_resistance)
#     Z1 = -_RTD_A
#     Z2 = _RTD_A * _RTD_A - (4 * _RTD_B)
#     Z3 = (4 * _RTD_B) / rtd_nominal
#     Z4 = 2 * _RTD_B
#     temp = Z2 + (Z3 * raw_reading)
#     temp = (math.sqrt(temp) + Z1) / Z4
#     if temp >= 0:
#         return temp
#
#     # For the following math to work, nominal RTD resistance must be normalized to 100 ohms
#     raw_reading /= rtd_nominal
#     raw_reading *= 100
#
#     rpoly = raw_reading
#     temp = -242.02
#     temp += 2.2228 * rpoly
#     rpoly *= raw_reading  # square
#     temp += 2.5859e-3 * rpoly
#     rpoly *= raw_reading  # ^3
#     temp -= 4.8260e-6 * rpoly
#     rpoly *= raw_reading  # ^4
#     temp -= 2.8183e-8 * rpoly
#     rpoly *= raw_reading  # ^5
#     temp += 1.5243e-10 * rpoly
#     return temp
#
#
# def decode_rtd_data(filtered_column_df, resistance_reference=400.0):
#     for i, sn in enumerate(filtered_column_df.columns):
#         filtered_column_df[f'Temp_{titles[i]}'] = filtered_column_df[sn].apply(
#             lambda row: None if not row or isinstance(row, bool) or len(row) < 4 or (row[3] << 8 | row[4]) & 1
#             else get_temperature(100.0, resistance_reference, ((row[3] << 8 | row[4]) >> 1)))
#
#     return filtered_column_df
#
#
# temperatures_df = decode_rtd_data(filtered_column_df)
#
# for col in temperatures_df.columns:
#     if col.startswith("Temp"):
#         temperatures_df[col] = temperatures_df[col].interpolate(method='linear', limit_direction='forward')  # Interpolate
#         temperatures_df[col] = temperatures_df[col].bfill()
#         temperatures_df[col] = temperatures_df[col].ffill()
#
# time_step = "300s"
#
# temperatures_df["Time"] = pd.date_range(start="2025-01-16 00:00", periods=len(temperatures_df), freq=time_step)
#
# plt.figure(figsize=(12, 6))
# for col in temperatures_df.columns:
#     if col.startswith("Temp"):
#         plt.plot(temperatures_df.index, temperatures_df[col], label=col)
#
# plt.title("Temperature Data Over Time (Custom Time Intervals)")
# plt.xlabel("Time")
# plt.ylabel("Temperature (°C)")
# plt.legend()
# plt.grid(True)
# plt.tight_layout()
# plt.show()

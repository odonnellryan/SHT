import math
import re
import matplotlib.pyplot as plt

import pandas as pd
from adafruit_max31865 import _RTD_A, _RTD_B

file_path = "c_arrays_received.txt"

with open(file_path, "r") as f:
    raw_data = f.read()

packet_matches = re.findall(r"char\s+\w+\[\]\s*=\s*\{([^}]*)\};", raw_data, re.DOTALL)

packets = []
for packet in packet_matches:
    byte_values = [int(h, 16) for h in re.findall(r"0x[0-9a-fA-F]{2}", packet)]
    packets.append(byte_values)

df = pd.DataFrame({"Packet": packets})

grouped_packets = [
    df.iloc[i:i + 100] for i in range(0, len(df), 100)
]

unique_groups = [group.drop_duplicates(subset=['Packet']) for group in grouped_packets]

rejoined_df = pd.concat(unique_groups, ignore_index=True)

allowed_sequences = [(17, 129, 18), (17, 129, 8), (17, 129, 9), (17, 129, 17)]

# storage (surface) is 9
# exhause is 8
# hot air is 2
# drum is 17

titles = ["Hot Air", "Exhaust", "Storage", "Drum"]

for i, seq in enumerate(allowed_sequences):
    rejoined_df[f'{titles[i]}'] = rejoined_df['Packet'].apply(
        lambda x: x if tuple(x[:len(seq)]) == seq else None
    )

filtered_column_df = rejoined_df[[f'{titles[i]}' for i in range(len(allowed_sequences))]]
filtered_column_df = filtered_column_df.dropna(how='all')


# rejoined_df['First_Two_Bytes'] = rejoined_df['Packet'].apply(lambda x: tuple(x[:3]) if len(x) >= 2 else None)
#
# filtered_df = rejoined_df.dropna(subset=['First_Two_Bytes'])
#
# counts = filtered_df['First_Two_Bytes'].value_counts()

def get_resistance(reading, reference_resistance):
    """Read the resistance of the RTD and return its value in Ohms."""
    resistance = reading
    resistance /= 32768
    resistance *= reference_resistance
    return resistance


def get_temperature(rtd_nominal, reference_resistance, reading):

    raw_reading = get_resistance(reading, reference_resistance)
    Z1 = -_RTD_A
    Z2 = _RTD_A * _RTD_A - (4 * _RTD_B)
    Z3 = (4 * _RTD_B) / rtd_nominal
    Z4 = 2 * _RTD_B
    temp = Z2 + (Z3 * raw_reading)
    temp = (math.sqrt(temp) + Z1) / Z4
    if temp >= 0:
        return temp

    # For the following math to work, nominal RTD resistance must be normalized to 100 ohms
    raw_reading /= rtd_nominal
    raw_reading *= 100

    rpoly = raw_reading
    temp = -242.02
    temp += 2.2228 * rpoly
    rpoly *= raw_reading  # square
    temp += 2.5859e-3 * rpoly
    rpoly *= raw_reading  # ^3
    temp -= 4.8260e-6 * rpoly
    rpoly *= raw_reading  # ^4
    temp -= 2.8183e-8 * rpoly
    rpoly *= raw_reading  # ^5
    temp += 1.5243e-10 * rpoly
    return temp


def decode_rtd_data(filtered_column_df, resistance_reference=400.0):
    for i, sn in enumerate(filtered_column_df.columns):
        filtered_column_df[f'Temp_{titles[i]}'] = filtered_column_df[sn].apply(
            lambda row: None if not row or isinstance(row, bool) or len(row) < 4 or (row[3] << 8 | row[4]) & 1
            else get_temperature(100.0, resistance_reference, ((row[3] << 8 | row[4]) >> 1)))

    return filtered_column_df


temperatures_df = decode_rtd_data(filtered_column_df)

for col in temperatures_df.columns:
    if col.startswith("Temp"):
        temperatures_df[col] = temperatures_df[col].interpolate(method='linear', limit_direction='forward')  # Interpolate
        temperatures_df[col] = temperatures_df[col].bfill()
        temperatures_df[col] = temperatures_df[col].ffill()

time_step = "300s"

temperatures_df["Time"] = pd.date_range(start="2025-01-16 00:00", periods=len(temperatures_df), freq=time_step)

plt.figure(figsize=(12, 6))
for col in temperatures_df.columns:
    if col.startswith("Temp"):
        plt.plot(temperatures_df.index, temperatures_df[col], label=col)

plt.title("Temperature Data Over Time (Custom Time Intervals)")
plt.xlabel("Time")
plt.ylabel("Temperature (°C)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
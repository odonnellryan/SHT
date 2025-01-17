import matplotlib.pyplot as plt
import pandas as pd

import get_data
from data_classes import convert_ir_to_temperature, decode_rtd_row

df = get_data.get_data_received()

ir_seqs = [(20,)]

df['IRSensor'] = df['Packet'].apply(
    lambda x: x if any(tuple(x[:len(seq)]) == seq for seq in ir_seqs) else None
)

ir_sensor = df['IRSensor'].dropna().reset_index(drop=True)

ir_sensor = pd.DataFrame({
    'IRSensor': ir_sensor,
    'Temperature': ir_sensor.apply(lambda x: convert_ir_to_temperature(x) if x else None)
})

# storage (surface) is 9
# exhause is 8
# hot air is 2
# drum is 17
# cooling is 32

control_sequences = [(14, 190), (14, 191), (14, 192), (14, 193), (14, 194), (14, 195), (14, 196), (14, 197), (14, 198),
                     (14, 199)]

allowed_sequences = [(17, 129, 18), (17, 129, 8), (17, 129, 9), (17, 129, 17), (17, 129, 32)]

unknown_sequences = [(20, 114, 3)]

# df['NotInTempSensorSequence'] = df['Packet'].apply(
#     lambda x: x if not any(
#         tuple(x[:len(seq)]) == seq for seq in allowed_sequences + ir_seqs + control_sequences) else None
# )

# not_in_temp_seq = df['NotInTempSensorSequence'].dropna()

titles = ["Hot Air", "Exhaust", "Storage", "Drum", "Cooling"]

for i, seq in enumerate(allowed_sequences):
    df[f'{titles[i]}'] = df['Packet'].apply(
        lambda x: x if tuple(x[:len(seq)]) == seq else None
    )

filtered_column_df = df[[f'{titles[i]}' for i in range(len(allowed_sequences))]]
filtered_column_df = filtered_column_df.dropna(how='all')


# rejoined_df['First_Two_Bytes'] = rejoined_df['Packet'].apply(lambda x: tuple(x[:3]) if len(x) >= 2 else None)
#
# filtered_df = rejoined_df.dropna(subset=['First_Two_Bytes'])
#
# counts = filtered_df['First_Two_Bytes'].value_counts()


def decode_rtd_data(filtered_column_df, resistance_reference=400.0):
    for sn in filtered_column_df:
        filtered_column_df[f'Temp_{sn}'] = filtered_column_df[sn].apply(
            lambda row: decode_rtd_row(row, resistance_reference)
        )
    return filtered_column_df


temperatures_df = decode_rtd_data(filtered_column_df)

for col in temperatures_df.columns:
    if col.startswith("Temp"):
        temperatures_df[col] = temperatures_df[col].interpolate(method='linear',
                                                                limit_direction='forward')  # Interpolate
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

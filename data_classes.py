import math
from collections import deque
from datetime import datetime

import tornado.log
from adafruit_max31865 import _RTD_A, _RTD_B

from packet_utils import Packet


def bytes_to_int_array(byte_sequence):
    return [int(f"{byte:02X}", 16) for byte in byte_sequence]


def bytes_to_control_value(byte_sequence):
    if not byte_sequence or len(byte_sequence) < 4:
        return None
    core_bytes = byte_sequence[2:-3]
    try:
        return [int(bytes(core_bytes[i:i + 2]).decode(), 16) for i in range(0, len(core_bytes), 2)][0]
    except Exception:
        return None


def convert_ir_to_temperature(data_array):
    def calc_celsius_temp(raw_temp):
        return (raw_temp * 0.02) - 273.75

    def convert_bytes_to_int(data):
        return (data[1] << 8) | data[0]

    if len(data_array) < 3:
        return None

    temp_bytes = data_array[3:5]

    raw_temp = convert_bytes_to_int(temp_bytes)
    return calc_celsius_temp(raw_temp)


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


def decode_rtd_row(row, resistance_reference):
    if not row or isinstance(row, bool) or len(row) < 4 or (row[3] << 8 | row[4]) & 1:
        return None
    return get_temperature(100.0, resistance_reference, ((row[3] << 8 | row[4]) >> 1))


def add_to_datapoints(cls, sensor_id, value):
    try:
        # if sensor_id == 17:
        #     tornado.log.app_log.info(f"Adding value {value} to sensor {sensor_id}, last value  {cls.mapper[sensor_id][-1] if cls.mapper[sensor_id] else None}")
        cls.mapper[sensor_id].append(value)
    except KeyError:
        return False
    return True


MAX_QUEUE_SIZE = 30


class ControlData:

    def __init__(self):
        self.drum_heater = deque(maxlen=MAX_QUEUE_SIZE)
        self.hot_air = deque(maxlen=MAX_QUEUE_SIZE)
        self.halogen = deque(maxlen=MAX_QUEUE_SIZE)
        self.monitor = deque(maxlen=MAX_QUEUE_SIZE)
        self.mapper = {
            (2, 51): self.drum_heater,
            (2, 49): self.hot_air,
            (2, 50): self.halogen,
            (2, 77): self.monitor
        }

    def __repr__(self):
        def format_last_values(data, n=5):
            return data[-n:] if len(data) > n else data

        return (
            f"ControlData(\n"
            f"  drum_heater: {format_last_values(self.drum_heater)},\n"
            f"  hot_air: {format_last_values(self.hot_air)},\n"
            f"  halogen: {format_last_values(self.halogen)},\n"
            f"  monitor: {format_last_values(self.monitor)}\n"
            f")"
        )

    def add_datapoint_from_bytes(self, b):
        try:
            data_array = bytes_to_int_array(b)
            data_array = data_array[2:]
            key_bytes = (data_array[0], data_array[1])
            control_value = bytes_to_control_value(data_array)
            if control_value:
                return add_to_datapoints(self, key_bytes, control_value)
        except IndexError:
            pass
        return False


class SensorData:

    def __init__(self):
        self.storage = deque(maxlen=MAX_QUEUE_SIZE)
        self.exhaust = deque(maxlen=MAX_QUEUE_SIZE)
        self.hot_air = deque(maxlen=MAX_QUEUE_SIZE)
        self.drum = deque(maxlen=MAX_QUEUE_SIZE)
        self.cooling = deque(maxlen=MAX_QUEUE_SIZE)
        self.ir = deque(maxlen=MAX_QUEUE_SIZE)
        self.ir_ambient = deque(maxlen=MAX_QUEUE_SIZE)

        self.mapper = {
            18: self.hot_air,
            8: self.exhaust,
            9: self.storage,
            17: self.drum,
            32: self.cooling
        }

    def __repr__(self):
        def format_last_values(data, n=5):
            return data[-n:] if len(data) > n else data

        return (
            f"SensorData(\n"
            f"  storage: {format_last_values(self.storage)},\n"
            f"  exhaust: {format_last_values(self.exhaust)},\n"
            f"  hot_air: {format_last_values(self.hot_air)},\n"
            f"  drum: {format_last_values(self.drum)},\n"
            f"  cooling: {format_last_values(self.cooling)},\n"
            f"  ir: {format_last_values(self.ir)},\n"
            f"  ir_ambient: {format_last_values(self.ir_ambient)}\n"
            f")"
        )

    def add_sensor_data(self, b):
        try:
            data_array = bytes_to_int_array(b)
            if data_array[0] == 20:
                ir_temp = convert_ir_to_temperature(data_array)
                if ir_temp and ir_temp <= 100:
                    self.ir_ambient.append(ir_temp)
                    return False
                if ir_temp:
                    self.ir.append(ir_temp)
                    return False
            else:
                first, second = data_array[0], data_array[1]
                if not (first == 17 and second == 129):
                    return False
                temp = decode_rtd_row(data_array, 400)

                if temp:
                    sensor_id = data_array[2]
                    v = add_to_datapoints(self, sensor_id, temp)

                    return v

        except IndexError:
            pass
        return False


def convert_to_datetime(timestamp_str):
    return datetime.strptime(timestamp_str, "%H:%M:%S.%f")


class Roaster:

    def __init__(self):
        self.control_data = ControlData()
        self.sensor_data = SensorData()

    def add_data_packet(self, data_packet: Packet):
        if data_packet.is_sending:
            self.control_data.add_datapoint_from_bytes(data_packet.byte_data)
        else:
            self.sensor_data.add_sensor_data(data_packet.byte_data)

    def __repr__(self):
        return (
            f"""
            Control Group:
                Control: {self.control_data}
                Sensors: {self.sensor_data} 
            """
        )

    def get_latest_for_artisan(self):
        return {
            'ET': round(self.sensor_data.storage[-1], 2) if self.sensor_data.storage else 0,
            'BT': round(self.sensor_data.drum[-1], 2) if self.sensor_data.drum else 0,
            'Hot Air': round(self.sensor_data.hot_air[-1], 2) if self.sensor_data.hot_air else 0,
            'Exhaust': round(self.sensor_data.exhaust[-1], 2) if self.sensor_data.exhaust else 0,
            'Cooling': round(self.sensor_data.cooling[-1], 2) if self.sensor_data.cooling else 0,
            'IR': round(self.sensor_data.ir[-1], 2) if self.sensor_data.ir else 0,
            'IR Ambient': round(self.sensor_data.ir_ambient[-1], 2) if self.sensor_data.ir_ambient else 0,
            'Drum Heater': round(self.control_data.drum_heater[-1], 2) if self.control_data.drum_heater else 0,
            'Hot Air Control': round(self.control_data.hot_air[-1], 2) if self.control_data.hot_air else 0,
            'Halogen Control': round(self.control_data.halogen[-1], 2) if self.control_data.halogen else 0,
            'Monitor Control': round(self.control_data.monitor[-1], 2) if self.control_data.monitor else 0,
        }

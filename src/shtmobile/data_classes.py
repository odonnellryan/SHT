import math
import time
from collections import deque
from datetime import datetime

_RTD_A = 3.9083e-3
_RTD_B = -5.775e-7

try:
    from shtmobile.packet_utils import Packet
except Exception:
    try:
        from packet_utils import Packet
    except ImportError:
        from src.shtmobile.packet_utils import Packet


class TimeBasedQueue(deque):
    def __init__(self, min_interval=100, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.min_interval = min_interval * 1_000_000
        self.max_gap = 100 * 1_000_000
        self.last_logged_time = 0
        self.last_value = None

    def append(self, item):
        current_time = time.time_ns()

        if self.last_logged_time and current_time - self.last_logged_time > self.max_gap:
            gap = current_time - self.last_logged_time
            num_interpolations = (gap // self.min_interval) - 1
            for i in range(1, num_interpolations + 1):
                interpolated_time = self.last_logged_time + i * self.min_interval
                interpolated_value = self._interpolate(self.last_value, item, i, num_interpolations + 1)
                super().append((interpolated_time, interpolated_value))

        if current_time - self.last_logged_time >= self.min_interval:
            super().append((current_time, item))
            self.last_logged_time = current_time
            self.last_value = item

    def _interpolate(self, start_value, end_value, step, total_steps):
        if start_value is None:
            return end_value
        return start_value + (end_value - start_value) * (step / total_steps)


def check_for_second_sequence(sub_sequence):
    for i, n in enumerate(sub_sequence):
        if i == 0:
            continue
        try:
            first, second = n, sub_sequence[i + 1]
        except IndexError:
            return None
        if first == 14 and str(second).startswith('19'):
            return i
    return None


def get_second_sequence_indexes_if_exists(sub_sequence, check_sequences):
    first_exists = False
    for i, sequence in enumerate(check_sequences):
        for j in range(len(sub_sequence) - 1):
            if first_exists:
                index = check_for_second_sequence(sub_sequence)
                if index is not None:
                    return index
            if sequence[0] == sub_sequence[j] and sequence[1] == sub_sequence[j + 1]:
                first_exists = True
    return None


def get_control_sequences(values):
    sub_sequences = []
    try:
        sub_sequences.extend(alt_get_subsequence(values))
    except IndexError:
        return sub_sequences
    return sub_sequences


def check_for_19star(v):
    return str(v).startswith("19") and len(str(v)) == 3


def add_twos_to_return_sequences(sequences):
    return_sequences = []
    for seq in sequences:
        if seq[0] == 14 and check_for_19star(seq[1]) and seq[2] != 2:
            return_sequences.append(
                seq[:2] + [2] + seq[2:]
            )
        else:
            return_sequences.append(seq)

    return return_sequences


def check_beginning_sequence(sequence, i):
    return (sequence[i] == 14 and check_for_19star(sequence[i + 1])) or (
            sequence[i] == 9 and sequence[i + 1] == 32)


def alt_get_subsequence(sequence):
    return_sequences = []

    i = 0
    while i < len(sequence):

        hit_endbyte = True
        v = []
        try:
            if check_beginning_sequence(sequence, i):
                v.extend([sequence[i], sequence[i + 1]])
                hit_endbyte = False
        except IndexError:
            continue
        while not hit_endbyte:
            try:
                if check_beginning_sequence(sequence, i):
                    i += 2
                if sequence[i] == 3:
                    hit_endbyte = True
                v.append(sequence[i])
                i += 1
            except IndexError:
                hit_endbyte = True
        if v:
            return_sequences.append(v)
        i += 1
    return add_twos_to_return_sequences(return_sequences)


def get_subsequence(sub_sequences):
    check_values = [
        51,
        49,
        50,
    ]

    cleaned_values = []
    i = 0
    counter = 0

    while i < len(sub_sequences):
        if sub_sequences[i] == 14 and check_for_19star(sub_sequences[i + 1]):
            if cleaned_values:
                cleaned_values[-1] = cleaned_values[-1][0:counter]

            if cleaned_values and (len(cleaned_values[-1]) == 4 or len(cleaned_values[-1]) == 5):
                if cleaned_values[-1][-1] in check_values and sub_sequences[i] == 14 and check_for_19star(
                        sub_sequences[i + 1]):
                    cleaned_values[-1] += sub_sequences[i + 2:]
                elif sub_sequences[i + 2] not in check_values:
                    cleaned_values[-1] += sub_sequences[i + 2:]
                else:
                    cleaned_values[-1] += sub_sequences[i:]
            else:
                if not sub_sequences[i + 2] == 2:
                    sub_sequences = sub_sequences[:i + 2] + [2] + sub_sequences[i + 2:]
                cleaned_values.append(sub_sequences[i:])
                counter = 0
        i += 1
        counter += 1
    return cleaned_values


def bytes_to_int_array(byte_sequence):
    return [int(f"{byte:02X}", 16) for byte in byte_sequence]


def bytes_to_control_value(byte_sequence):
    # remove "stop" byte - but strangely it is not always there...
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
        cls.mapper[sensor_id].append(value)
    except KeyError:
        return
    return


def calculate_drum_steps(arry):
    try:
        first, second = f"{arry[2]:02X}", f"{arry[3]:02X}"
        if first == 0 and second == 0:
            return 0
        value = int(f"{first}{second}", 16)
    except IndexError:
        return None

    start_value = 63274
    step_size = 6140
    val = ((start_value - value) // step_size) + 2
    if val > 10:
        return 1
    return val


MAX_QUEUE_SIZE = 100


def get_continuation_array(sequence, prior_array):
    for i, v in enumerate(sequence):
        if v == 14 and str(sequence[i + 1]).startswith('19'):
            if (len(prior_array) > 3 and prior_array[2]) != 2 and sequence[i + 2] != 2:
                new_seq = sequence[i:2] + [2] + sequence[i + 2:]
                return new_seq
            return sequence[i:]
    return []


class ControlData:

    def __init__(self):
        self.drum_heater = deque(maxlen=MAX_QUEUE_SIZE)
        self.hot_air = deque(maxlen=MAX_QUEUE_SIZE)
        self.halogen = deque(maxlen=MAX_QUEUE_SIZE)
        self.drum_speed = deque(maxlen=MAX_QUEUE_SIZE)
        self.mapper = {
            (2, 51): self.drum_heater,
            (2, 49): self.hot_air,
            (2, 50): self.halogen,
        }
        self._prev_val = None

    def __repr__(self):
        def format_last_values(data, n=5):
            return data[-n:] if len(data) > n else data

        return (
            f"ControlData(\n"
            f"  drum_heater: {format_last_values(self.drum_heater)},\n"
            f"  hot_air: {format_last_values(self.hot_air)},\n"
            f"  halogen: {format_last_values(self.halogen)},\n"
            f")"
        )

    def get_datapoint_and_control_value(self, data_array):
        try:
            data_array = bytes_to_int_array(data_array)

            if self._prev_val is not None:
                data_array = self._prev_val + data_array
            else:
                if data_array[0] == 14 and check_for_19star(data_array[1]):
                    self._prev_val = data_array

            control_sequences = get_control_sequences(data_array)

            rv = []

            if any(c[-1] == 3 for c in control_sequences):
                self._prev_val = None

            for c in control_sequences:
                if c[0] == 9 and c[1] == 32:
                    self.drum_speed.append(calculate_drum_steps(c))
                else:
                    try:
                        key_bytes = (c[2], c[3])
                    except IndexError:
                        continue
                    rv.append((key_bytes, bytes_to_control_value(c)))
            try:
                if rv and any([r[1] is not None for r in rv]):
                    self._prev_val = None
            except IndexError:
                print("i1")
            return rv

        except IndexError:
            print("i1")

        return []

    def add_datapoint_from_bytes(self, b):
        for key_bytes, control_value in self.get_datapoint_and_control_value(b):
            if control_value is not None:
                add_to_datapoints(self, key_bytes, control_value)


class SensorData:

    def __init__(self):
        self.storage = deque(maxlen=MAX_QUEUE_SIZE)
        self.exhaust = deque(maxlen=MAX_QUEUE_SIZE)
        self.hot_air = deque(maxlen=MAX_QUEUE_SIZE)
        self.drum = deque(maxlen=MAX_QUEUE_SIZE)
        self.cooling = deque(maxlen=MAX_QUEUE_SIZE)

        self.ir = deque(maxlen=MAX_QUEUE_SIZE)
        self.ir_ambient = deque(maxlen=MAX_QUEUE_SIZE)

        self.time_storage = TimeBasedQueue(maxlen=MAX_QUEUE_SIZE)
        self.time_exhaust = TimeBasedQueue(maxlen=MAX_QUEUE_SIZE)
        self.time_hot_air = TimeBasedQueue(maxlen=MAX_QUEUE_SIZE)
        self.time_drum = TimeBasedQueue(maxlen=MAX_QUEUE_SIZE)
        self.time_ir = TimeBasedQueue(maxlen=MAX_QUEUE_SIZE)

        self.time_mapper = {
            18: self.time_hot_air,
            8: self.time_exhaust,
            9: self.time_storage,
            17: self.time_drum
        }

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
                if self.drum and self.drum[-1] and abs(self.drum[-1] - ir_temp) < 10:
                    self.ir.append(ir_temp)
                    self.time_ir.append(ir_temp)
                    return
                if ir_temp and ir_temp <= 100:
                    self.ir_ambient.append(ir_temp)
                    return
                if ir_temp:
                    self.ir.append(ir_temp)
                    self.time_ir.append(ir_temp)
                    return
            else:
                first, second = data_array[0], data_array[1]
                if not (first == 17 and second == 129):
                    return
                temp = decode_rtd_row(data_array, 400)

                if temp:
                    sensor_id = data_array[2]
                    add_to_datapoints(self, sensor_id, temp)
                    try:
                        self.time_mapper[sensor_id].append(temp)
                    except KeyError:
                        pass
                    return

        except IndexError:
            pass
        return


def convert_to_datetime(timestamp_str):
    return datetime.strptime(timestamp_str, "%H:%M:%S.%f")


class Roaster:

    def __init__(self):
        self.control_data = ControlData()
        self.sensor_data = SensorData()

    def has_dropped_roast(self):
        # sensor_data.time_storage = TimeBasedQueue(maxlen=MAX_QUEUE_SIZE)
        # sensor_data.time_exhaust = TimeBasedQueue(maxlen=MAX_QUEUE_SIZE)
        # sensor_data.time_hot_air = TimeBasedQueue(maxlen=MAX_QUEUE_SIZE)
        # sensor_data.time_drum = TimeBasedQueue(maxlen=MAX_QUEUE_SIZE)
        # sensor_data.time_ir = TimeBasedQueue(maxlen=MAX_QUEUE_SIZE)
        # max queue size is 100, items are 100ms apart
        #
        # this should return true if all the following conditions are met, and if there are at least
        # 100 items in each of the sensors EXCEPT ir - we don't need IR to be full (but it needs to have some values)
        # 1) a major spike/increase in the storage temp, a degree in less than a second
        # 2) self.control_data.hot_air is set to 0 or None, when it had a prior value
        # 3) rapid decline in exhaust temp, a degree in less than a second
        # 4) almost immediate drop in IR temp, 2 degrees in less than a second
        if not all(len(queue) >= MAX_QUEUE_SIZE for queue in [
            self.sensor_data.time_storage,
            self.sensor_data.time_exhaust,
            self.sensor_data.time_hot_air,
            self.sensor_data.time_drum
        ]) or not len(self.sensor_data.time_ir) > 5:
            return False

        if self.sensor_data.time_storage[-1] - self.sensor_data.time_storage[-6] < 1:
            return False

        if self.control_data.hot_air and self.control_data.hot_air[-1] != 0 and any(
                v > 0 for v in self.control_data.hot_air):
            return False

        if self.sensor_data.time_exhaust[-6] - self.sensor_data.time_exhaust[-1] < 1:
            return False

        if self.sensor_data.time_ir[-4] - self.sensor_data.time_ir[-1] < 2:
            return False

        return True

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
            'Drum Speed': round(self.control_data.drum_speed[-1], 2) if self.control_data.drum_speed else 0,
        }

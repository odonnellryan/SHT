import random
import unittest
from collections import deque

from src.shtmobile.data_classes import ControlData




def _perf_control_test(self, test_data):
    c = ControlData()
    for test_val, data_sequences in test_data:
        hit_test = False
        for data_seq in data_sequences:
            contvs = c.get_datapoint_and_control_value(data_seq)
            if contvs and contvs[0] and contvs[0][1] is not None:
                self.assertEquals(contvs[0][1], test_val)
                hit_test = True
        if not hit_test:
            if test_val != 'THIS SHOULD NOT RETURN':
                self.fail(f"Should have hit test case for {test_val}")


class TestControlSequences(unittest.TestCase):
    def test_hot_air(self):
        test_data = [

            (15,
             (
                 [20, 2, 90, 1, 3, 7, 14, 198, 2, 49, 48, 70, 65, 55, 3, 17, 145, 194, 1, 2, 1],
             ),
             ),

            (85,
             (
                 [14, 197, 2, 49, 53, 53, 57, 66],
             ),
             ),

            (75,
             (
                 [14, 195, 2, 49, 52, 66, 14, 194, 65, 55, 3],

             ),
             ),

            (90, ([20, 2, 90, 1, 3, 7, 17, 145, 194, 1, 2, 1, 14, 197, 2, 49, 53, 65, 65, 55, 14, 192, 3],),),
            (25,
             ([14, 192, 2, 49],
              [14, 196, 49, 57, 57, 66, 3, 4, 116, 20, 2, 90, 1, 3, 7, 17, 145, 194, 1, 2, 1]),
             ),
            (45,
             ([14, 193, 2, 49],
              [14, 196, 50, 68, 65, 55, 3, 20, 2, 90, 1, 3, 7, 17, 145, 194, 1, 2, 1]),
             ),
            (80, (
                [14, 192, 2],
                [14, 197, 49, 53, 48, 57, 54, 3, 17, 145, 194, 1, 2, 1, 4, 116, 20, 2, 90, 1, 3, 7],
            )),
            (55, (
                [14, 193, 2, 49],
                [14, 196, 51, 55, 57, 66, 3, 17, 145, 194, 1, 2, 1, 4, 116, 4, 1, 20, 2, 90, 1, 3, 7],
            )),
            (40, (
                [14, 193, 2, 49],
                [20, 2, 3, 83, 73, 205],
                [14, 196, 50, 56, 57, 66, 3],
            )),
            (0, ([14, 193, 2, 49, 14, 196, 48, 48, 57, 49, 3, 17, 145, 194, 1, 2, 1],)),
            ('THIS SHOULD NOT RETURN', (
                [14, 192, 49, 14, 192, 52, 14, 192, 49, 14, 192, 57, 14, 192, 54, 14, 192, 3],
            )),
        ]

        _perf_control_test(self, test_data)

    def test_roast_drop(self):

        class TempSensor:
            def __init__(self, max_queue_size):
                self.ir = deque(maxlen=max_queue_size)

            def check_sudden_drop(self):
                if len(self.ir) < self.ir.maxlen:
                    return False

                slopes = [self.ir[i + 1] - self.ir[i] for i in range(len(self.ir) - 1)]
                midpoint = len(slopes) // 2

                if any(slope < min(slopes[:midpoint]) - 4 for slope in slopes[midpoint:]):
                    return True

                return False

        def generate_gradual_incline(max_length, noise_level=1):
            base_value = random.randint(20, 30)
            return [base_value + i + random.uniform(-noise_level, noise_level) for i in range(max_length)]

        def generate_wobbly_data(max_length, noise_level=20):
            base_value = random.randint(20, 30)
            return [base_value + random.uniform(-noise_level, noise_level) for _ in range(max_length)]

        sensor = TempSensor(30)

        # Gradual incline, no drop
        sensor.ir.extend(generate_gradual_incline(30))
        assert not sensor.check_sudden_drop(), "Failed: Should not detect a drop in gradual incline."

        # Lots of wobble, no significant drop
        sensor.ir.extend(generate_wobbly_data(30))
        assert not sensor.check_sudden_drop(), "Failed: Should not detect a drop with consistent wobble."

        # Wobble with a drop in the second half
        sensor.ir.extend(generate_gradual_incline(30 // 2) +
                         [50] + [random.uniform(45, 35) for _ in range(30 // 2 - 1)])
        assert sensor.check_sudden_drop(), "Failed: Should detect a drop in the second half."

        print("All test cases passed.")
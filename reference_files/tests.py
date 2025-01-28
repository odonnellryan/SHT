import random
import unittest
from collections import deque

from src.shtmobile.data_classes import ControlData, get_subsequence, bytes_to_control_value, alt_get_subsequence


def _perf_control_test(self, test_data):
    c = ControlData()
    for test_val, data_sequences in test_data:
        hit_test = False
        for data_seq in data_sequences:
            contvs = c.get_datapoint_and_control_value(data_seq)
            for v in contvs:
                if v[1] == test_val:
                    self.assertTrue(True)
                    hit_test = True
        if not hit_test:
            if test_val != 'THIS SHOULD NOT RETURN':
                self.fail(f"Should have hit test case for {test_val}")


class TestControlSequences(unittest.TestCase):

    def test_get_subsequence(self):

        t1 =(
            [20, 2, 90, 1, 3, 7, 14, 198, 2, 49, 48, 70, 65, 55, 3, 17, 145, 194, 1, 2, 1],
            [[14, 198, 2, 49, 48, 70, 65, 55, 3]]
        )
        t2 = (
            [14, 197, 49, 53, 48, 57, 54, 3, 17, 145, 14, 198, 2, 49, 48, 70, 65, 55, 3],
            [[14, 197, 2, 49, 53, 48, 57, 54, 3], [14, 198, 2, 49, 48, 70, 65, 55, 3]]
        )
        t3 = (
            [20, 2, 90, 1, 3, 7, 17, 145, 194, 1, 2, 1, 14, 193, 2, 49, 14, 196, 49, 69, 65, 55, 3],
            [[14, 193, 2, 49, 49, 69, 65, 55, 3]]
        )
        t4 = ([14, 194, 2, 49, 48, 14, 195, 70, 65, 55, 3],
              [[14, 194, 2, 49, 48, 70, 65, 55, 3]]
            )
        t5 = ([14, 197, 2, 49, 53, 53, 57, 66],
              [[14, 197, 2, 49, 53, 53, 57, 66]])

        t1 = alt_get_subsequence([14, 198, 2, 49, 51, 67, 65, 55, 3])

        sub1 = alt_get_subsequence(t1[0])
        sub2 = alt_get_subsequence(t2[0])
        sub3 = alt_get_subsequence(t3[0])
        sub4 = alt_get_subsequence(t4[0])
        sub5 = alt_get_subsequence(t5[0])
        self.assertEquals(sub1, t1[1])
        self.assertEquals(sub2, t2[1])
        self.assertEquals(sub3, t3[1])
        self.assertEquals(sub4, t4[1])
        self.assertEquals(sub5, t5[1])
        pass

    def test_hot_air(self):
        test_data = [
            (60,
             ([
                 [14, 192, 3],
                 [14, 198, 2, 49, 51, 67, 65, 55, 3]
             ])
             ),
            (45,
             ([
                 [14, 193, 51, 3, 17, 145, 194, 1, 2, 1, 20, 2, 90, 1, 3, 7],
                 [14, 193, 2, 49, 14, 196, 50, 68, 65, 55, 3]
             ])),
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
             ([14, 192, 2, 49, 49, 57, 57, 66, 3],)),
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
                [14, 196, 50, 56, 57, 66, 3],
            )),
            (0, ([14, 193, 2, 49, 14, 196, 48, 48, 57, 49, 3, 17, 145, 194, 1, 2, 1],)),
            ('THIS SHOULD NOT RETURN', (
                [14, 192, 49, 14, 192, 3],
            )),
            (75, (
                [14, 192, 2, 14, 197, 49, 52, 66, 65, 55, 3],
            )),
            (30, (
                [20, 2, 90, 1, 3, 7, 17, 145, 194, 1, 2, 1, 14, 193, 2, 49, 14, 196, 49, 69, 65, 55, 3],
            )),
            (15, (
                [14, 194, 2, 49, 48, 14, 195, 70, 65, 55, 3],
            ))
        ]


        cv = bytes_to_control_value([14, 198, 2, 49, 51, 67, 65, 55, 3])

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

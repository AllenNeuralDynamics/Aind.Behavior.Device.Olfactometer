import subprocess
import sys
import unittest

import numpy as np
import pandas as pd
from aind_behavior_services.rig.olfactometer import OlfactometerChannelConfig, OlfactometerChannelType

from aind_behavior_device_olfactometer.analysis import DeviceData, RawSession, process
from aind_behavior_device_olfactometer.task_logic import OlfactometerCalibrationParameters

FLOW = 100.0
BLOCK = 40.0  # seconds allotted to each (device, channel) block: end-valve mode, then odor-valve mode
SAMPLE_PERIOD = 0.01


def make_session(
    channels: tuple[tuple[int, int], ...] = ((0, 0),),
    n_repeats: int = 3,
    n_found: int | None = None,
    flow: float = FLOW,
    has_end_session: bool = True,
) -> RawSession:
    """Synthetic session: each (device, channel) runs end-valve mode then odor-valve mode, 2 s on / 2 s off."""
    n_found = n_repeats if n_found is None else n_found
    time = np.arange(0, BLOCK * len(channels), SAMPLE_PERIOD)
    pid = pd.Series(0.0, index=time)
    events, modes = [], []
    valve = {d: [] for d, _ in channels}
    target = {d: pd.DataFrame(0.0, index=[0.0], columns=[f"Channel{i}" for i in range(5)]) for d, _ in channels}
    actual = {d: {i: pd.Series(0.0, index=time) for i in range(5)} for d, _ in channels}

    for block, (device, channel) in enumerate(channels):
        for is_end_valve, t_config in ((True, block * BLOCK), (False, block * BLOCK + BLOCK / 2)):
            config = OlfactometerChannelConfig(
                channel_index=channel, channel_type=OlfactometerChannelType.ODOR, flow_rate=FLOW, odorant="test"
            )
            events.append((t_config, device, config))
            modes.append((t_config, is_end_valve))
            for repeat in range(n_found):
                t_on = t_config + 1 + 4 * repeat
                t_off = t_on + 2
                pid[(time >= t_on) & (time < t_off)] = 100.0
                if is_end_valve:
                    valve[device] += [(t_on, True), (t_off, False)]
                else:
                    target[device].loc[t_on, f"Channel{channel}"] = FLOW
                    target[device].loc[t_off, f"Channel{channel}"] = 0.0
                actual[device][channel][(time >= t_on) & (time < t_off)] = flow

    devices = {}
    for device, transitions in valve.items():
        times, states = zip(*sorted(transitions)) if transitions else ((), ())
        devices[device] = DeviceData(
            target_flow=target[device].sort_index(),
            actual_flow=actual[device],
            end_valve=pd.Series(list(states), index=list(times), dtype=bool),
        )
    return RawSession(
        pid=pid,
        devices=devices,
        odor_channels=pd.DataFrame(
            {"device_index": [e[1] for e in events], "config": [e[2] for e in events]},
            index=[e[0] for e in events],
        ),
        end_valve_mode=pd.Series([m[1] for m in modes], index=[m[0] + 0.005 for m in modes]),
        task_parameters=OlfactometerCalibrationParameters(n_repeats_per_stimulus=n_repeats),
        has_end_session=has_end_session,
    )


def failed(processed) -> set[str]:
    return {c.name for c in processed.checks if not c.passed}


class ProcessingTests(unittest.TestCase):
    def test_segmentation(self):
        processed = process(make_session())
        self.assertEqual(failed(processed), set())
        self.assertEqual(len(processed.calibrations), 2)
        for cal in processed.calibrations:
            self.assertEqual([r.index for r in cal.repeats], [0, 1, 2])
            for repeat in cal.repeats:
                self.assertAlmostEqual(repeat.t_off - repeat.t_on, 2.0)
                self.assertAlmostEqual(repeat.pid.index[0], -0.2, places=1)
                self.assertAlmostEqual(repeat.pid.index[-1], 2.5, places=1)
                self.assertEqual(repeat.pid[repeat.pid.index < 0].max(), 0.0)

    def test_mode_split(self):
        processed = process(make_session())
        self.assertEqual({c.mode for c in processed.calibrations}, {"end_valve", "odor_valve"})
        self.assertEqual(len(processed.metrics), 6)
        self.assertEqual(set(processed.metrics["mode"]), {"end_valve", "odor_valve"})
        self.assertTrue(np.allclose(processed.metrics["pid_delta"], 100.0))
        self.assertTrue(np.allclose(processed.metrics["flow_mean"], FLOW, rtol=0.01))

    def test_extension_keying(self):
        processed = process(make_session(channels=((0, 1), (1, 1), (1, 2))))
        keys = {(c.device_index, c.channel_index, c.mode) for c in processed.calibrations}
        self.assertEqual(len(keys), 6)
        self.assertIn((1, 1, "odor_valve"), keys)
        self.assertEqual(failed(processed), set())
        self.assertTrue(all(len(c.repeats) == 3 for c in processed.calibrations))

    def test_missing_repeat_fails(self):
        processed = process(make_session(n_found=2))
        self.assertEqual(failed(processed), {"expected_repeats_found"})

    def test_missing_repeat_does_not_borrow_next_block(self):
        processed = process(make_session(channels=((0, 0), (0, 1)), n_found=2))
        self.assertEqual([len(c.repeats) for c in processed.calibrations], [2, 2, 2, 2])
        self.assertEqual(failed(processed), {"expected_repeats_found"})

    def test_flow_off_target_fails(self):
        processed = process(make_session(flow=50.0))
        self.assertEqual(failed(processed), {"flow_within_tolerance"})

    def test_missing_end_session_fails(self):
        processed = process(make_session(has_end_session=False))
        self.assertEqual(failed(processed), {"end_session_exists"})

    def test_no_odor_channels_fails(self):
        raw = make_session()
        raw.odor_channels = raw.odor_channels.iloc[0:0]
        self.assertIn("odor_channels_configured", failed(process(raw)))


class BoundaryTests(unittest.TestCase):
    def test_analysis_imports_without_io_libraries(self):
        code = (
            "import sys\n"
            "class Blocker:\n"
            "    def find_spec(self, name, path=None, target=None):\n"
            "        if name.split('.')[0] in {'contraqctor', 'harp', 'matplotlib'}:\n"
            "            raise ImportError(name)\n"
            "sys.meta_path.insert(0, Blocker())\n"
            "import aind_behavior_device_olfactometer.analysis\n"
        )
        result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()

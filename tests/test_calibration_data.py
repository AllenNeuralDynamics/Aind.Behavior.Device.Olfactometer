import unittest
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

from aind_behavior_device_olfactometer.analysis import process
from aind_behavior_device_olfactometer.data_contract import dataset
from aind_behavior_device_olfactometer.data_qc._adapter import raw_session_from_dataset

BUCKET_URL = "https://aind-open-data.s3.amazonaws.com"
SESSION = "calibration_2026-10-09_13-57-50"
CACHE_DIR = Path(__file__).parent / ".cache"


def download_session() -> Path:
    listing = urllib.request.urlopen(f"{BUCKET_URL}/?list-type=2&prefix={SESSION}/", timeout=30).read()
    keys = [e.text for e in ET.fromstring(listing).iter("{http://s3.amazonaws.com/doc/2006-03-01/}Key")]
    for key in keys:
        target = CACHE_DIR / key
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            urllib.request.urlretrieve(f"{BUCKET_URL}/{urllib.parse.quote(key)}", target)
    return CACHE_DIR / SESSION


class CalibrationSessionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            root = download_session()
        except OSError as e:
            raise unittest.SkipTest(f"Public calibration data unavailable: {e}")
        data = dataset(root)
        data.load_all(strict=False)
        cls.raw = raw_session_from_dataset(data)
        cls.processed = process(cls.raw)

    def test_channels_found(self):
        keys = {(c.device_index, c.channel_index, c.mode) for c in self.processed.calibrations}
        expected = {(0, channel, mode) for channel in range(3) for mode in ("end_valve", "odor_valve")}
        self.assertEqual(keys, expected)
        self.assertEqual(list(self.raw.devices), [0])

    def test_repeats(self):
        self.assertEqual(self.raw.task_parameters.n_repeats_per_stimulus, 3)
        self.assertTrue(all(len(c.repeats) == 3 for c in self.processed.calibrations))

    def test_checks_pass(self):
        self.assertTrue(all(c.passed for c in self.processed.checks), self.processed.checks)

    def test_metrics(self):
        metrics = self.processed.metrics
        self.assertEqual(len(metrics), 18)
        self.assertTrue((metrics["pid_delta"] > 100).all(), metrics["pid_delta"])
        self.assertTrue(((metrics["flow_mean"] - metrics["flow_target"]).abs() < 2).all(), metrics["flow_mean"])
        time_on = self.raw.task_parameters.time_on
        self.assertTrue(((metrics["duration"] - time_on).abs() < 0.05).all(), metrics["duration"])


if __name__ == "__main__":
    unittest.main()

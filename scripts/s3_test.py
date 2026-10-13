import argparse
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

from aind_behavior_device_olfactometer.analysis import process
from aind_behavior_device_olfactometer.data_contract import dataset
from aind_behavior_device_olfactometer.data_qc._adapter import raw_session_from_dataset
from aind_behavior_device_olfactometer.data_qc.data_qc import make_channel_figures

S3_NS = "{http://s3.amazonaws.com/doc/2006-03-01/}"


def download(location: str, cache: Path) -> Path:
    """Downloads a public s3://bucket/asset to cache/asset, skipping files already there."""
    bucket, asset = re.fullmatch(r"s3://([^/]+)/(.+?)/*", location).groups()
    base = f"https://{bucket}.s3.amazonaws.com"
    keys, token = [], None
    while True:
        url = f"{base}/?list-type=2&prefix={urllib.parse.quote(asset)}/"
        if token:
            url += f"&continuation-token={urllib.parse.quote(token)}"
        root = ET.fromstring(urllib.request.urlopen(url, timeout=30).read())
        keys += [e.text for e in root.iter(f"{S3_NS}Key")]
        token = root.findtext(f"{S3_NS}NextContinuationToken")
        if token is None:
            break
    for key in keys:
        target = cache / key
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            urllib.request.urlretrieve(f"{base}/{urllib.parse.quote(key)}", target)
    return cache / asset


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the calibration analysis on an S3 session and save the plots.")
    parser.add_argument("location", nargs="?", default="s3://aind-open-data/calibration_2026-10-09_13-57-50")
    parser.add_argument("--cache", type=Path, default=Path(".cache"))
    parser.add_argument("--out", type=Path, default=Path("s3_test_output"))
    args = parser.parse_args()

    t = time.perf_counter()
    root = download(args.location, args.cache)
    print(f"downloaded {root} in {time.perf_counter() - t:.2f} s")

    t = time.perf_counter()
    processed = process(raw_session_from_dataset(dataset(root)))
    print(f"loaded and processed in {time.perf_counter() - t:.2f} s")
    for check in processed.checks:
        print(f"  {'PASS' if check.passed else 'FAIL'} {check.name}: {check.message}")

    args.out.mkdir(parents=True, exist_ok=True)
    for fig in make_channel_figures(processed):
        path = args.out / f"{fig.get_suptitle().split(' (')[0].replace(' ', '_').lower()}.png"
        fig.savefig(path)
        print(f"  wrote {path}")
    return 0 if all(c.passed for c in processed.checks) else 1


if __name__ == "__main__":
    sys.exit(main())

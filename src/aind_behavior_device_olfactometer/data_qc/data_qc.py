import argparse
import typing as t
from functools import cached_property
from pathlib import Path

import matplotlib.pyplot as plt
from contraqctor import contract, qc
from contraqctor.contract.harp import HarpDevice
from contraqctor.qc._context_extensions import ContextExportableObj

from ..analysis import ProcessedSession, process
from ..data_contract import dataset
from ._adapter import raw_session_from_dataset
from ._plot import plot_channel


class DeviceOlfactometerQcSuite(qc.Suite):
    def __init__(self, dataset: contract.Dataset):
        self.dataset = dataset

    @cached_property
    def processed(self) -> ProcessedSession:
        return process(raw_session_from_dataset(self.dataset))

    def _check(self, name: str):
        result = next(c for c in self.processed.checks if c.name == name)
        return self.pass_test(None, result.message) if result.passed else self.fail_test(None, result.message)

    def test_end_session_exists(self):
        """Check that the session has an end event."""
        return self._check("end_session_exists")

    def test_odor_channels_configured(self):
        """Check that at least one odor channel was configured."""
        return self._check("odor_channels_configured")

    def test_expected_repeats_found(self):
        """Check that every (device, channel, mode) has the expected number of repeats."""
        return self._check("expected_repeats_found")

    def test_flow_within_tolerance(self):
        """Check that the mean flow of every repeat is close to the target flow."""
        return self._check("flow_within_tolerance")

    def test_plot_channels(self):
        """Generate calibration plots for each odor channel and export as assets."""
        figs = make_channel_figures(self.processed)
        if not figs:
            return self.fail_test(None, "No odor channel configurations found in the dataset.")
        return self.pass_test(
            None,
            f"Generated calibration plots for {len(figs)} channel(s).",
            context=ContextExportableObj.as_context(figs),
        )


def make_channel_figures(processed: ProcessedSession) -> list[plt.Figure]:
    channels: dict[tuple[int, int], list] = {}
    for cal in processed.calibrations:
        channels.setdefault((cal.device_index, cal.channel_index), []).append(cal)
    figs = []
    for calibrations in channels.values():
        fig, _ = plot_channel(calibrations, processed.raw.task_parameters.n_repeats_per_stimulus)
        fig.set_size_inches(10, 6)
        figs.append(fig)
    return figs


def make_qc_runner(dataset: contract.Dataset) -> qc.Runner:
    _runner = qc.Runner()
    dataset.load_all(strict=False)
    exclude: list[contract.DataStream] = []

    # Exclude commands to Harp boards as these are tested separately
    for cmd in dataset["Behavior"]["HarpCommands"]:
        for stream in cmd:
            if isinstance(stream, contract.harp.HarpRegister):
                exclude.append(stream)

    # Add the outcome of the dataset loading step to the automatic qc
    _runner.add_suite(qc.contract.ContractTestSuite(dataset.collect_errors(), exclude=exclude), group="Data contract")

    # Add Harp tests for ALL Harp devices in the dataset
    for stream in (_r := dataset["Behavior"]):
        if isinstance(stream, HarpDevice):
            commands = t.cast(HarpDevice, _r["HarpCommands"][stream.name])
            _runner.add_suite(qc.harp.HarpDeviceTestSuite(stream, commands), stream.name)

    # Also add the HarpOlfactometerExtension if it exists, as it may not be present in all sessions and is not a HarpDevice itself but contains them
    dataset["Behavior"]["HarpOlfactometerExtension"].load()
    dataset["Behavior"]["HarpCommands"]["HarpOlfactometerExtension"].load()

    for stream in dataset["Behavior"]["HarpOlfactometerExtension"]:
        if isinstance(stream, HarpDevice):
            commands = t.cast(HarpDevice, dataset["Behavior"]["HarpCommands"]["HarpOlfactometerExtension"][stream.name])
            _runner.add_suite(qc.harp.HarpDeviceTestSuite(stream, commands), stream.name)

    # Add Harp Hub tests
    all_harp_devices = [harp_device for harp_device in dataset["Behavior"] if isinstance(harp_device, HarpDevice)]
    all_harp_devices.extend(
        [
            harp_device
            for harp_device in dataset["Behavior"]["HarpOlfactometerExtension"]
            if isinstance(harp_device, HarpDevice)
        ]
    )
    _runner.add_suite(
        qc.harp.HarpHubTestSuite(
            dataset["Behavior"]["HarpClockGenerator"],
            all_harp_devices,
        ),
        "HarpHub",
    )

    # Add Csv tests
    csv_streams = [stream for stream in dataset.iter_all() if isinstance(stream, contract.csv.Csv)]
    for stream in csv_streams:
        _runner.add_suite(qc.csv.CsvTestSuite(stream), stream.name)

    # Add the DeviceOlfactometer specific tests
    _runner.add_suite(DeviceOlfactometerQcSuite(dataset), "DeviceOlfactometer")
    return _runner


def main():
    parser = argparse.ArgumentParser(description="Process olfactometer data.")
    parser.add_argument("--path", type=str, help="Path to the dataset root directory", required=True)
    args = parser.parse_args()
    data = dataset(Path(args.path))
    data.load_all()
    make_channel_figures(process(raw_session_from_dataset(data)))
    plt.show()


if __name__ == "__main__":
    main()

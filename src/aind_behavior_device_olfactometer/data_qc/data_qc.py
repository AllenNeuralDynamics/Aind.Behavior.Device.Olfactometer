import typing as t

import pandas as pd
from contraqctor import contract, qc
from contraqctor.contract.harp import HarpDevice
from contraqctor.qc._context_extensions import ContextExportableObj


class DeviceOlfactometerQcSuite(qc.Suite):
    def __init__(self, dataset: contract.Dataset):
        from ._utils import ProcessedData

        self._processed_data = ProcessedData.from_dataset(dataset)
        self.dataset = dataset

    def test_end_session_exists(self):
        """Check that the session has an end event."""
        end_session = self.dataset["Behavior"]["SoftwareEvents"]["EndSession"]

        if not end_session.has_data:
            return self.fail_test(
                None, "EndSession event does not exist. Session may be corrupted or not ended properly."
            )

        assert isinstance(end_session.data, pd.DataFrame)
        if end_session.data.empty:
            return self.fail_test(None, "No data in EndSession. Session may be corrupted or not ended properly.")
        else:
            return self.pass_test(None, "EndSession event exists with data.")

    def test_plot_channels(self):
        """Generate calibration plots for each odor channel and export as assets."""
        from ._utils import plot_channel

        processed = self._processed_data
        channel_groups = list(processed.odor_channel_config.groupby(["channel_index"]))

        if not channel_groups:
            return self.fail_test(None, "No odor channel configurations found in the dataset.")

        figs = []
        for _, channel_df in channel_groups:
            fig, _ = plot_channel(channel_df, self.dataset)
            fig.set_size_inches(10, 6)
            figs.append(fig)

        return self.pass_test(
            None,
            f"Generated calibration plots for {len(figs)} channel(s).",
            context=ContextExportableObj.as_context(figs),
        )


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

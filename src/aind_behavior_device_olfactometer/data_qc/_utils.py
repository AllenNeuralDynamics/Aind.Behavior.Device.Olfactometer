import argparse
import typing
import typing as t
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Literal, cast

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from aind_behavior_services.rig import olfactometer as olf
from contraqctor import contract, qc
from contraqctor.contract import Dataset, DataStream
from contraqctor.contract.harp import HarpDevice
from contraqctor.qc._context_extensions import ContextExportableObj
from matplotlib.colors import LinearSegmentedColormap

from ..data_contract import dataset
from ..task_logic import OlfactometerCalibrationLogic

if typing.TYPE_CHECKING:
    pass

plt.style.use("dark_background")


@dataclass
class ProcessedData:
    _parent_dataset_ref: Dataset = field(repr=False)
    pid: pd.Series = field(init=False)
    end_valve_state: pd.Series = field(init=False)
    odor_mixture: pd.Series = field(init=False)
    flowmeter: pd.Series = field(init=False)
    odor_channel_config: pd.Series = field(init=False)

    @classmethod
    def from_dataset(cls, parent_dataset: "Dataset") -> "ProcessedData":
        _p = cls(_parent_dataset_ref=parent_dataset)
        _p.pid = load_pid(_p._parent_dataset_ref)
        _p.end_valve_state = load_end_valve_state(_p._parent_dataset_ref)
        _p.odor_mixture = load_odor_mixture(_p._parent_dataset_ref)
        _p.flowmeter = load_flowmeter(_p._parent_dataset_ref)
        _p.odor_channel_config = load_odor_channel_configuration(_p._parent_dataset_ref)
        return _p


class ProcessedDataStream(DataStream[ProcessedData, Dataset]):
    @staticmethod
    def _reader(params: Dataset) -> ProcessedData:
        return ProcessedData.from_dataset(params)


def append_processed_data(dataset: Dataset):
    dataset.add_stream(
        ProcessedDataStream(
            name="Processed",
            description="Processed data from the Olfactometer calibration procedure",
            reader_params=dataset,
        )
    )


def load_pid(
    dataset: Dataset, channel: Literal["Channel0", "Channel1", "Channel2", "Channel3"] = "Channel0"
) -> pd.Series:
    _data = dataset["Behavior"]["HarpAnalogInput"]["AnalogData"].data
    return _data[_data["MessageType"] == "EVENT"][channel]


def load_end_valve_state(dataset: Dataset, channel: Literal["EndValve0", "EndValve1"] = "EndValve0") -> pd.Series:
    _data = dataset["Behavior"]["HarpOlfactometer"]["EndValveState"].data
    return _data[_data.shift() != _data]


def load_odor_mixture(dataset: Dataset) -> pd.Series:
    target_flow = dataset["Behavior"]["HarpOlfactometer"]["ChannelsTargetFlow"].data
    target_flow = target_flow[target_flow["MessageType"] == "WRITE"]
    return target_flow


def load_flowmeter(dataset: Dataset) -> List[pd.Series]:
    channel_data: List[pd.Series] = []
    for i in range(5):
        _channel_reg = f"Channel{i}ActualFlow"
        _data = dataset["Behavior"]["HarpOlfactometer"][_channel_reg].data
        channel_data.append(_data[_data["MessageType"] == "EVENT"][_channel_reg])
    return channel_data


def load_odor_channel_configuration(dataset: Dataset, tolerance_seconds: float = 0.01) -> pd.DataFrame:
    _is_end_valve: pd.DataFrame = dataset["Behavior"]["IsEndValveCalibration"].data

    _odor_config: pd.DataFrame = dataset["Behavior"]["SoftwareEvents"]["OdorChannel"].data
    _odor_config["data_parsed"] = _odor_config["data"].apply(lambda x: olf.OlfactometerChannelConfig.model_validate(x))
    _odor_config = _odor_config["data_parsed"]

    merged_df = pd.merge_asof(
        _odor_config.sort_index(),
        _is_end_valve.sort_index(),
        left_index=True,
        right_index=True,
        tolerance=tolerance_seconds,
        direction="nearest",
    )
    merged_df.rename(inplace=True, columns={"data": "is_end_valve_calibration", "data_parsed": "odor_channel_config"})
    merged_df["channel_index"] = merged_df["odor_channel_config"].apply(lambda x: x.channel_index)
    merged_df["channel_type"] = merged_df["odor_channel_config"].apply(lambda x: x.channel_type)
    merged_df["odorant"] = merged_df["odor_channel_config"].apply(lambda x: x.odorant)

    merged_df = merged_df[merged_df["channel_type"] == olf.OlfactometerChannelType.ODOR]

    return merged_df


def stream_window(event: float, stream: pd.Series, window: tuple[float, float] = (-1, 1)) -> pd.Series:
    return stream[(stream.index >= event + window[0]) & (stream.index <= event + window[1])]


def stream_slice(event: tuple[float, float], stream: pd.Series, window: tuple[float, float] = (-1, 1)) -> pd.Series:
    return stream[(stream.index >= event[0] + window[0]) & (stream.index <= event[1] + window[1])]


def plot_channel(
    df: pd.DataFrame, dataset: Dataset, window: tuple[float, float] = (-0.2, 0.5)
) -> tuple[plt.Figure, plt.Axes]:
    task_logic: OlfactometerCalibrationLogic = dataset["Behavior"]["InputSchemas"]["TaskLogic"].data
    expected_repeats = task_logic.task_parameters.n_repeats_per_stimulus
    cmap = LinearSegmentedColormap.from_list("blue_to_yellow", ["blue", "yellow"], expected_repeats)
    channel_config: olf.OlfactometerChannelConfig = df.iloc[0].odor_channel_config

    fig, ax = plt.subplots(2, 2, sharex=True)
    processed = cast(ProcessedData, dataset["Processed"].data)

    for env_valve_mode, mode_df in df.groupby(["is_end_valve_calibration"]):
        t = mode_df.index[0]

        if env_valve_mode[0] == 1:
            # if end_valve_calibration we use the valve state to find the start and end of each trial
            _plt_col = 0
            _start = processed.end_valve_state[
                (processed.end_valve_state.index >= t) & (processed.end_valve_state == 1)
            ].head(expected_repeats)
            _end = processed.end_valve_state[
                (processed.end_valve_state.index >= _start.index[0]) & (processed.end_valve_state == 0)
            ].head(expected_repeats)

        else:
            _plt_col = 1
            _channel = olf.OlfactometerChannel(channel_config.channel_index).name
            _odor_mix = processed.odor_mixture[_channel]

            _start = _odor_mix[(_odor_mix.index >= t) & (_odor_mix > 0)].head(expected_repeats)
            _end = _odor_mix[(_odor_mix.index >= _start.index[0]) & (_odor_mix == 0)].head(expected_repeats)

        color_iter = iter(cmap(np.linspace(0, 1, expected_repeats)))
        for t_on, t_off in zip(_start.index, _end.index):
            pid_slice = stream_slice((t_on, t_off), processed.pid, window)
            flowmeter_slice = stream_slice((t_on, t_off), processed.flowmeter[channel_config.channel_index], window)

            _color = next(color_iter)
            ax[0, _plt_col].plot(pid_slice.index - t_on, pid_slice, color=_color)
            ax[0, _plt_col].set_ylabel("PID Signal (AdcUnits)")
            ax[0, _plt_col].grid(True)
            ax[0, _plt_col].set_title("End Valve Calibration" if env_valve_mode[0] == 1 else "Odor Valve Calibration")

            ax[1, _plt_col].plot(flowmeter_slice.index - t_on, flowmeter_slice, color=_color)
            ax[1, _plt_col].set_ylabel("Flow Rate (ml/min)")
            ax[1, _plt_col].set_ylim(0, 150)
            ax[1, _plt_col].set_xlabel("Time (s)")
            ax[1, _plt_col].grid(True)

        # Improve overall figure aesthetics

    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.suptitle(
        f"Channel {channel_config.channel_index} ({channel_config.odorant}) @ {channel_config.flow_rate} ml/min"
    )
    return fig, ax


class DeviceOlfactometerQcSuite(qc.Suite):
    def __init__(self, dataset: contract.Dataset):
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
        processed = ProcessedData.from_dataset(self.dataset)
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

    # Add Harp Hub tests
    _runner.add_suite(
        qc.harp.HarpHubTestSuite(
            dataset["Behavior"]["HarpClockGenerator"],
            [harp_device for harp_device in dataset["Behavior"] if isinstance(harp_device, HarpDevice)],
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
    append_processed_data(data)
    data.load_all()

    for _, valve_calibration_df in cast(ProcessedDataStream, data["Processed"]).data.odor_channel_config.groupby(
        ["channel_index"]
    ):
        fig = plot_channel(valve_calibration_df, data)[0]
        fig.set_size_inches(10, 6)
        plt.show()
    return None


if __name__ == "__main__":
    main()

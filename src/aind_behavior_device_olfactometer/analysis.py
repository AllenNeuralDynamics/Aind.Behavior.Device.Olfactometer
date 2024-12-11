import argparse
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Literal

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from aind_behavior_core_analysis.io._core import DataStreamCollection
from aind_behavior_core_analysis.io.data_stream import (
    DataStreamCollectionFromFilePattern,
    HarpDataStreamCollectionFactory,
    SoftwareEventStream,
)
from aind_behavior_services.calibration import olfactometer as olf
from aind_behavior_services.utils import model_from_json_file
from matplotlib.colors import LinearSegmentedColormap

from aind_behavior_device_olfactometer.rig import OlfactometerCalibrationRig
from aind_behavior_device_olfactometer.task_logic import OlfactometerCalibrationLogic

plt.style.use("dark_background")


@dataclass
class ProcessedData:
    _parent_dataset_ref: "Dataset" = field(repr=False)
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


@dataclass
class Dataset:
    root_path: Path
    analog_input: DataStreamCollection = field(init=False)
    olfactometer: DataStreamCollection = field(init=False)
    software_events: DataStreamCollection = field(init=False)
    metadata_task_logic: OlfactometerCalibrationLogic = field(init=False)
    metadata_rig: OlfactometerCalibrationRig = field(init=False)
    processed_data: ProcessedData = field(init=False)

    def __post_init__(self):
        self.analog_input = HarpDataStreamCollectionFactory(
            path=self.root_path / "behavior" / "AnalogInput.harp", default_inference_mode="register_0"
        ).build()
        self.olfactometer = HarpDataStreamCollectionFactory(
            path=self.root_path / "behavior" / "Olfactometer.harp", default_inference_mode="register_0"
        ).build()
        self.software_events = DataStreamCollectionFromFilePattern(
            path=self.root_path / "behavior" / "SoftwareEvents", pattern="*.json", stream_type=SoftwareEventStream
        ).build()
        self.metadata_task_logic = model_from_json_file(
            self.root_path / "behavior" / "Logs" / "tasklogic_input.json", OlfactometerCalibrationLogic
        )
        self.metadata_rig = model_from_json_file(
            self.root_path / "behavior" / "Logs" / "rig_input.json", OlfactometerCalibrationRig
        )

    def make_processed_data(self):
        self.processed_data = ProcessedData.from_dataset(self)


def load_pid(
    dataset: Dataset, channel: Literal["Channel0", "Channel1", "Channel2", "Channel3"] = "Channel0"
) -> pd.Series:
    _data = dataset.analog_input["AnalogData"].load()
    return _data[_data["MessageType"] == "EVENT"][channel]


def load_end_valve_state(dataset: Dataset, channel: Literal["EndValve0", "EndValve1"] = "EndValve0") -> pd.Series:
    _data = dataset.olfactometer["EndValveState"].load()[channel]
    return _data[_data.shift() != _data]


def load_odor_mixture(dataset: Dataset) -> pd.Series:
    target_flow = dataset.olfactometer["ChannelsTargetFlow"].reload()
    target_flow = target_flow[target_flow["MessageType"] == "WRITE"]
    return target_flow


def load_flowmeter(dataset: Dataset) -> List[pd.Series]:
    channel_data: List[pd.Series] = []
    for i in range(5):
        _channel_reg = f"Channel{i}ActualFlow"
        _data = dataset.olfactometer[_channel_reg].load()
        channel_data.append(_data[_data["MessageType"] == "EVENT"][_channel_reg])
    return channel_data


def load_odor_channel_configuration(dataset: Dataset, tolerance_seconds: float = 0.01) -> pd.DataFrame:
    _is_end_valve = dataset.software_events["IsEndValveCalibration"].reload()["data"]

    _odor_config = dataset.software_events["OdorChannel"].reload()
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
    expected_repeats = dataset.metadata_task_logic.task_parameters.n_repeats_per_stimulus
    cmap = LinearSegmentedColormap.from_list("blue_to_yellow", ["blue", "yellow"], expected_repeats)
    channel_config: olf.OlfactometerChannelConfig = df.iloc[0].odor_channel_config

    fig, ax = plt.subplots(2, 2, sharex=True)

    for env_valve_mode, mode_df in df.groupby(["is_end_valve_calibration"]):
        t = mode_df.index[0]

        if env_valve_mode[0] == 1:
            # if end_valve_calibration we use the valve state to find the start and end of each trial
            _plt_col = 0
            _start = dataset.processed_data.end_valve_state[
                (dataset.processed_data.end_valve_state.index >= t) & (dataset.processed_data.end_valve_state == 1)
            ].head(expected_repeats)
            _end = dataset.processed_data.end_valve_state[
                (dataset.processed_data.end_valve_state.index >= _start.index[0])
                & (dataset.processed_data.end_valve_state == 0)
            ].head(expected_repeats)

        else:
            _plt_col = 1
            _channel = olf.OlfactometerChannel(channel_config.channel_index).name
            _odor_mix = dataset.processed_data.odor_mixture[_channel]

            _start = _odor_mix[(_odor_mix.index >= t) & (_odor_mix > 0)].head(expected_repeats)
            _end = _odor_mix[(_odor_mix.index >= _start.index[0]) & (_odor_mix == 0)].head(expected_repeats)

        color_iter = iter(cmap(np.linspace(0, 1, expected_repeats)))
        for t_on, t_off in zip(_start.index, _end.index):
            pid_slice = stream_slice((t_on, t_off), dataset.processed_data.pid, window)
            flowmeter_slice = stream_slice(
                (t_on, t_off), dataset.processed_data.flowmeter[channel_config.channel_index], window
            )

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


def main():
    parser = argparse.ArgumentParser(description="Process olfactometer data.")
    parser.add_argument("--path", type=str, help="Path to the dataset root directory", required=True)
    args = parser.parse_args()
    data = Dataset(Path(args.path))
    data.make_processed_data()

    for _, valve_calibration_df in data.processed_data.odor_channel_config.groupby(["channel_index"]):
        fig = plot_channel(valve_calibration_df, data)[0]
        fig.set_size_inches(10, 6)
        plt.show()
    return None


if __name__ == "__main__":
    main()

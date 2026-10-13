import json
import re

import pandas as pd
from aind_behavior_services.rig.olfactometer import OlfactometerChannelConfig
from contraqctor.contract import Dataset, DataStream
from contraqctor.contract.harp import HarpDevice

from ..analysis.models import DeviceData, RawSession
from ..task_logic import OlfactometerCalibrationParameters

N_CHANNELS = 5


def raw_session_from_dataset(dataset: Dataset) -> RawSession:
    behavior = dataset["Behavior"]
    odor_events = _data(behavior["SoftwareEvents"]["OdorChannel"])["data"]
    odor_channels = pd.DataFrame(
        {
            "device_index": odor_events.apply(lambda x: x["Item1"]),
            "config": odor_events.apply(lambda x: OlfactometerChannelConfig.model_validate(x["Item2"])),
        }
    )
    end_session = behavior["Logs"]["EndSession"]
    return RawSession(
        pid=_event_column(_data(behavior["HarpAnalogInput"]["AnalogData"]), "Channel0"),
        devices={index: _device_data(device) for index, device in _olfactometers(dataset).items()},
        odor_channels=odor_channels,
        end_valve_mode=_data(behavior["SoftwareEvents"]["IsEndValveCalibration"])["data"].astype(bool),
        task_parameters=_task_parameters(behavior["InputSchemas"]["TaskLogic"]),
        has_end_session=end_session.has_data and not end_session.data.empty,
    )


def _data(stream: DataStream):
    if not stream.has_data:
        stream.load()
    return stream.data


def _olfactometers(dataset: Dataset) -> dict[int, HarpDevice]:
    behavior = dataset["Behavior"]
    devices = {0: behavior["HarpOlfactometer"]}
    extensions = behavior["HarpOlfactometerExtension"]
    _data(extensions)
    for device in extensions:
        devices[int(re.search(r"OlfactometerExtension(\d+)", device.name).group(1))] = device
    return devices


def _device_data(device: HarpDevice) -> DeviceData:
    target_flow = _data(device["ChannelsTargetFlow"])
    end_valve = _data(device["EndValveState"])
    return DeviceData(
        target_flow=target_flow[target_flow["MessageType"] == "WRITE"].drop(columns="MessageType"),
        actual_flow={
            i: _event_column(_data(device[f"Channel{i}ActualFlow"]), f"Channel{i}ActualFlow") for i in range(N_CHANNELS)
        },
        end_valve=end_valve[end_valve["MessageType"] == "WRITE"]["EndValve0"],
    )


def _event_column(data: pd.DataFrame, column: str) -> pd.Series:
    return data[data["MessageType"] == "EVENT"][column]


def _task_parameters(stream: DataStream) -> OlfactometerCalibrationParameters:
    # Only the parameters are validated; the full task logic carries a version literal that breaks on older sessions.
    with open(stream.reader_params.path, encoding="utf-8") as f:
        return OlfactometerCalibrationParameters.model_validate(json.load(f)["task_parameters"])

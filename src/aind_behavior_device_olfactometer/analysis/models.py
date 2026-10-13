from dataclasses import dataclass, field
from typing import Literal

import pandas as pd
from aind_behavior_services.rig.olfactometer import OlfactometerChannelConfig

from ..task_logic import OlfactometerCalibrationParameters

CalibrationMode = Literal["end_valve", "odor_valve"]


@dataclass
class DeviceData:
    """Streams from one olfactometer. All indexes are harp time in seconds."""

    target_flow: pd.DataFrame  # ChannelsTargetFlow WRITE messages, columns Channel0..Channel4
    actual_flow: dict[int, pd.Series]  # channel index -> ChannelNActualFlow EVENT messages
    end_valve: pd.Series  # EndValve0 state (bool), WRITE messages


@dataclass
class RawSession:
    """Everything the analysis needs from one calibration session. Produced by an I/O adapter."""

    pid: pd.Series  # AnalogInput AnalogData Channel0, EVENT messages
    devices: dict[int, DeviceData]  # 0 = main olfactometer, N = OlfactometerExtensionN
    odor_channels: pd.DataFrame  # OdorChannel events: columns device_index, config (OlfactometerChannelConfig)
    end_valve_mode: pd.Series  # IsEndValveCalibration events (bool)
    task_parameters: OlfactometerCalibrationParameters
    has_end_session: bool


@dataclass
class Repeat:
    index: int
    t_on: float
    t_off: float
    pid: pd.Series  # indexed by time relative to t_on
    flow: pd.Series  # indexed by time relative to t_on


@dataclass
class ChannelCalibration:
    device_index: int
    channel_index: int
    mode: CalibrationMode
    config: OlfactometerChannelConfig
    repeats: list[Repeat] = field(default_factory=list)


@dataclass
class CheckResult:
    name: str
    passed: bool
    message: str


@dataclass
class ProcessedSession:
    raw: RawSession
    calibrations: list[ChannelCalibration]
    metrics: pd.DataFrame  # one row per (device_index, channel_index, mode, repeat)
    checks: list[CheckResult]

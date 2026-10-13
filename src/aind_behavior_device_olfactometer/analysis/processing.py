import numpy as np
import pandas as pd
from aind_behavior_services.rig.olfactometer import OlfactometerChannelType

from .checks import run_checks
from .models import CalibrationMode, ChannelCalibration, ProcessedSession, RawSession, Repeat

_MERGE_TOLERANCE_SECONDS = 0.01


def process(raw: RawSession, window: tuple[float, float] = (-0.2, 0.5)) -> ProcessedSession:
    rows = [] if raw.odor_channels.empty else _odor_channel_modes(raw).itertuples()
    calibrations = [_calibrate(raw, row, window) for row in rows]
    processed = ProcessedSession(raw=raw, calibrations=calibrations, metrics=_metrics(calibrations), checks=[])
    processed.checks = run_checks(processed)
    return processed


def stream_slice(stream: pd.Series, t_start: float, t_stop: float) -> pd.Series:
    return stream.loc[t_start:t_stop]


def _odor_channel_modes(raw: RawSession) -> pd.DataFrame:
    """First OdorChannel event per (device, channel, mode), with the mode taken from the nearest end-valve event
    and t_next the start of the following stimulus block."""
    events = raw.odor_channels.sort_index()
    modes = raw.end_valve_mode.sort_index().rename("is_end_valve").to_frame()
    merged = pd.merge_asof(
        events, modes, left_index=True, right_index=True, tolerance=_MERGE_TOLERANCE_SECONDS, direction="nearest"
    )
    merged = merged.dropna(subset=["is_end_valve"])
    merged["channel_index"] = merged["config"].apply(lambda c: c.channel_index)
    merged = merged[merged["config"].apply(lambda c: c.channel_type == OlfactometerChannelType.ODOR)]
    merged["mode"] = np.where(merged["is_end_valve"].astype(bool), "end_valve", "odor_valve")
    merged["t_config"] = merged.index
    merged = merged.drop_duplicates(["device_index", "channel_index", "mode"]).reset_index(drop=True)
    merged["t_next"] = merged["t_config"].shift(-1, fill_value=np.inf)
    return merged


def _calibrate(raw: RawSession, row, window: tuple[float, float]) -> ChannelCalibration:
    mode: CalibrationMode = row.mode
    calibration = ChannelCalibration(
        device_index=row.device_index, channel_index=row.channel_index, mode=mode, config=row.config
    )
    device = raw.devices.get(row.device_index)
    if device is None:
        return calibration

    if mode == "end_valve":
        state = device.end_valve.astype(bool)
    else:
        state = device.target_flow[f"Channel{row.channel_index}"] > 0
    flow = device.actual_flow.get(row.channel_index, pd.Series(dtype=float))

    n_repeats = raw.task_parameters.n_repeats_per_stimulus
    for index, (t_on, t_off) in enumerate(_on_off_times(state, row.t_config, row.t_next)[:n_repeats]):
        pid = stream_slice(raw.pid, t_on + window[0], t_off + window[1])
        flow_slice = stream_slice(flow, t_on + window[0], t_off + window[1])
        calibration.repeats.append(
            Repeat(
                index=index,
                t_on=t_on,
                t_off=t_off,
                pid=pid.set_axis(pid.index - t_on),
                flow=flow_slice.set_axis(flow_slice.index - t_on),
            )
        )
    return calibration


def _on_off_times(state: pd.Series, t_start: float, t_stop: float) -> list[tuple[float, float]]:
    """(t_on, t_off) of each on-period of a boolean state that starts within [t_start, t_stop)."""
    state = state.astype(bool)
    changed = state != state.shift(fill_value=False)
    on = state.index[changed & state & (state.index >= t_start) & (state.index < t_stop)]
    off = state.index[changed & ~state]
    times = []
    for t_on in on:
        later_off = off[off > t_on]
        if len(later_off) == 0:
            break
        times.append((float(t_on), float(later_off[0])))
    return times


def _metrics(calibrations: list[ChannelCalibration]) -> pd.DataFrame:
    rows = []
    for cal in calibrations:
        for repeat in cal.repeats:
            baseline = repeat.pid[repeat.pid.index < 0].mean()
            peak = repeat.pid[repeat.pid.index >= 0].max()
            on_flow = repeat.flow[(repeat.flow.index >= 0) & (repeat.flow.index <= repeat.t_off - repeat.t_on)]
            rows.append(
                {
                    "device_index": cal.device_index,
                    "channel_index": cal.channel_index,
                    "mode": cal.mode,
                    "repeat": repeat.index,
                    "pid_baseline": baseline,
                    "pid_peak": peak,
                    "pid_delta": peak - baseline,
                    "flow_mean": on_flow.mean(),
                    "flow_target": cal.config.flow_rate,
                    "duration": repeat.t_off - repeat.t_on,
                }
            )
    columns = [
        "device_index",
        "channel_index",
        "mode",
        "repeat",
        "pid_baseline",
        "pid_peak",
        "pid_delta",
        "flow_mean",
        "flow_target",
        "duration",
    ]
    return pd.DataFrame(rows, columns=columns)

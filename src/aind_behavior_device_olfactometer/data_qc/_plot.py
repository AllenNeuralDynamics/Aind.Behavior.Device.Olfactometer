import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

from ..analysis.models import ChannelCalibration

plt.style.use("dark_background")

_COLUMNS = {"end_valve": 0, "odor_valve": 1}
_TITLES = {"end_valve": "End Valve Calibration", "odor_valve": "Odor Valve Calibration"}


def plot_channel(calibrations: list[ChannelCalibration], n_repeats: int) -> tuple[plt.Figure, plt.Axes]:
    """Plot the repeats of every mode of one (device, channel)."""
    cmap = LinearSegmentedColormap.from_list("blue_to_yellow", ["blue", "yellow"], n_repeats)
    colors = cmap(np.linspace(0, 1, n_repeats))
    fig, ax = plt.subplots(2, 2, sharex=True)

    for cal in calibrations:
        col = _COLUMNS[cal.mode]
        for repeat, color in zip(cal.repeats, colors):
            ax[0, col].plot(repeat.pid.index, repeat.pid, color=color)
            ax[1, col].plot(repeat.flow.index, repeat.flow, color=color)
        ax[0, col].set_title(_TITLES[cal.mode])

    for col in range(2):
        ax[0, col].set_ylabel("PID Signal (AdcUnits)")
        ax[0, col].grid(True)
        ax[1, col].set_ylabel("Flow Rate (ml/min)")
        ax[1, col].set_ylim(0, 150)
        ax[1, col].set_xlabel("Time (s)")
        ax[1, col].grid(True)

    config = calibrations[0].config
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.suptitle(
        f"Device {calibrations[0].device_index} channel {config.channel_index} ({config.odorant}) "
        f"@ {config.flow_rate} ml/min"
    )
    return fig, ax

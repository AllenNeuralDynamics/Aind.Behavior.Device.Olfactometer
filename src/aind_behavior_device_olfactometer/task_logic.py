from typing import Dict, Literal

from aind_behavior_services.rig import olfactometer as olf
from aind_behavior_services.task import Task, TaskParameters
from pydantic import Field

from . import __version__


class OlfactometerCalibrationParameters(TaskParameters):
    channel_config: Dict[olf.OlfactometerChannel, olf.OlfactometerChannelConfig] = Field(
        default_factory=dict, description="Configuration of olfactometer channels"
    )
    full_flow_rate: float = Field(default=1000, ge=0, le=1000, description="Full flow rate of the olfactometer")
    n_repeats_per_stimulus: int = Field(default=1, ge=1, description="Number of repeats per stimulus")
    time_on: float = Field(default=1, ge=0, description="Time (s) the valve is open during calibration")
    time_off: float = Field(default=1, ge=0, description="Time (s) the valve is close during calibration")


class OlfactometerCalibrationLogic(Task):
    """Olfactometer operation control model that is used to run a calibration data acquisition workflow"""

    name: str = Field(default="OlfactometerCalibration", title="Name of the task logic", frozen=True)
    version: Literal[__version__] = __version__
    task_parameters: OlfactometerCalibrationParameters = Field(title="Task parameters", validate_default=True)

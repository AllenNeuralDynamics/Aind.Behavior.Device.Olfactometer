from typing import List, Literal

from aind_behavior_services.rig import olfactometer as olf
from aind_behavior_services.task import Task, TaskParameters
from pydantic import BaseModel, Field

from . import __semver__


class ChannelToCalibrate(BaseModel):
    odor_index: int = Field(
        title="Olfactometer odor channel index. This is an absolute count across all olfactometer channels"
    )
    odor_configuration: olf.OlfactometerChannelConfig = Field(title="Olfactometer channel configuration")


class OlfactometerCalibrationParameters(TaskParameters):
    channel_config: List[ChannelToCalibrate] = Field(
        default_factory=list, description="List of olfactometer channels to calibrate with their configurations"
    )
    full_flow_rate: float = Field(default=1000, ge=0, le=1000, description="Full flow rate of the olfactometer")
    n_repeats_per_stimulus: int = Field(default=1, ge=1, description="Number of repeats per stimulus")
    time_on: float = Field(default=1, ge=0, description="Time (s) the valve is open during calibration")
    time_off: float = Field(default=1, ge=0, description="Time (s) the valve is close during calibration")


class OlfactometerCalibrationLogic(Task):
    """Olfactometer operation control model that is used to run a calibration data acquisition workflow"""

    name: str = Field(default="OlfactometerCalibration", title="Name of the task logic", frozen=True)
    version: Literal[__semver__] = __semver__
    task_parameters: OlfactometerCalibrationParameters = Field(title="Task parameters", validate_default=True)

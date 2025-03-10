from typing import Literal

from aind_behavior_services import rig
from aind_behavior_services.calibration import olfactometer as olf
from pydantic import Field

__version__ = "0.2.0"


class HarpOlfactometer(rig.HarpOlfactometer):
    """Overrides the default settings for the olfactometer calibration"""

    calibration: olf.OlfactometerCalibration = Field(description="Olfactometer calibration")


class OlfactometerCalibrationRig(rig.AindBehaviorRigModel):
    version: Literal[__version__] = __version__
    harp_olfactometer: HarpOlfactometer = Field(..., title="Olfactometer device")
    harp_analog_input: rig.HarpAnalogInput = Field(..., title="Analog input device")
    harp_clock_generator: rig.HarpWhiteRabbit = Field(..., title="Clock generator device")

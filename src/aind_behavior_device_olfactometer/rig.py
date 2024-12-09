from typing import Literal, Optional

from aind_behavior_services.calibration import olfactometer as olf
from aind_behavior_services.rig import AindBehaviorRigModel
from pydantic import Field

__version__ = "0.1.0"


class Olfactometer(olf.HarpOlfactometer):
    calibration: Optional[olf.OlfactometerCalibration] = Field(default=None, title="Calibration of the olfactometer")


class OlfactometerCalibrationRig(AindBehaviorRigModel):
    version: Literal[__version__] = __version__
    harp_olfactometer: Olfactometer = Field(..., title="Olfactometer device")
    harp_analog_input: olf.HarpAnalogInput = Field(..., title="Analog input device")
    harp_clock_generator: olf.HarpClockGenerator = Field(..., title="Clock generator device")

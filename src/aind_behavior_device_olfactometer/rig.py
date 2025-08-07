from typing import Literal

from aind_behavior_services import rig
from aind_behavior_services.calibration import olfactometer as olf
from pydantic import Field

from . import __version__


class OlfactometerCalibrationRig(rig.AindBehaviorRigModel):
    version: Literal[__version__] = __version__
    harp_olfactometer: olf.Olfactometer = Field(..., title="Olfactometer device")
    harp_analog_input: rig.harp.HarpAnalogInput = Field(..., title="Analog input device")
    harp_clock_generator: rig.harp.HarpWhiteRabbit = Field(..., title="Clock generator device")

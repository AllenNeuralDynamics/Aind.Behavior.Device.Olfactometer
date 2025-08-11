import datetime
from typing import Literal, Optional

import aind_behavior_services.calibration.aind_manipulator as man
from aind_behavior_services import rig
from aind_behavior_services.calibration import olfactometer as olf
from pydantic import Field

from . import __version__


class AlicatFlowmeter(rig.Device):
    device_type: Literal["AlicatFlowmeter"] = "AlicatFlowmeter"
    port_name: str = Field(..., description="Device port name")
    device_id: str = Field("A", description="Alicat device ID")
    pooling_period: datetime.timedelta = Field(
        datetime.timedelta(seconds=0.2), description="Device pooling interval in seconds"
    )


class OlfactometerCalibrationRig(rig.AindBehaviorRigModel):
    version: Literal[__version__] = __version__
    harp_olfactometer: olf.Olfactometer = Field(..., title="Olfactometer device")
    harp_analog_input: rig.harp.HarpAnalogInput = Field(..., title="Analog input device")
    harp_clock_generator: rig.harp.HarpWhiteRabbit = Field(..., title="Clock generator device")
    harp_manipulator: man.AindManipulatorDevice = Field(..., description="Manipulator")
    flowmeter: Optional[AlicatFlowmeter] = Field(default=None, description="Alicat flowmeter device")

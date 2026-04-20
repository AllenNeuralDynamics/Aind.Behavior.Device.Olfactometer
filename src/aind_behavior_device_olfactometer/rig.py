from typing import Literal, Optional

import aind_behavior_services.rig.aind_manipulator as man
from aind_behavior_services import rig
from aind_behavior_services.rig import harp
from aind_behavior_services.rig import olfactometer as olf
from pydantic import Field

from . import __semver__


class AlicatFlowmeter(rig.Device):
    device_type: Literal["AlicatFlowmeter"] = "AlicatFlowmeter"
    port_name: str = Field(description="Device port name")
    device_id: str = Field(default="A", description="Alicat device ID")
    pooling_period: float = Field(default=0.2, gt=0, description="Device pooling interval in seconds")


class OlfactometerCalibrationRig(rig.Rig):
    version: Literal[__semver__] = __semver__
    harp_olfactometer: olf.Olfactometer = Field(title="Olfactometer device")
    harp_olfactometer_extension: list[olf.Olfactometer] = Field(
        default_factory=list,
        description="A collection of subordinate olfactometers that can be added to increase the number of independently delivered odors. The order of the list determines the order by which odors are numbered",
    )
    harp_analog_input: harp.HarpAnalogInput = Field(title="Analog input device")
    harp_clock_generator: harp.HarpWhiteRabbit = Field(title="Clock generator device")
    harp_manipulator: man.AindManipulator = Field(description="Manipulator")
    flowmeter: Optional[AlicatFlowmeter] = Field(default=None, description="Alicat flowmeter device")

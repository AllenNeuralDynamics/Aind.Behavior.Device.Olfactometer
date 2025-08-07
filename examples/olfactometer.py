import os

from aind_behavior_services.base import get_commit_hash
from aind_behavior_services.calibration import aind_manipulator as man
from aind_behavior_services.calibration import olfactometer as olf
from aind_behavior_services.rig.harp import HarpAnalogInput, HarpWhiteRabbit
from aind_behavior_services.session import AindBehaviorSessionModel
from aind_behavior_services.utils import utcnow

from aind_behavior_device_olfactometer import rig, task_logic

channels_config = {
    olf.OlfactometerChannel.Channel0: olf.OlfactometerChannelConfig(
        channel_index=olf.OlfactometerChannel.Channel0,
        channel_type=olf.OlfactometerChannelType.ODOR,
        flow_rate=100,
        odorant="Banana",
        odorant_dilution=0.1,
    ),
    olf.OlfactometerChannel.Channel3: olf.OlfactometerChannelConfig(
        channel_index=olf.OlfactometerChannel.Channel3, channel_type=olf.OlfactometerChannelType.CARRIER, odorant="Air"
    ),
}

calibration = olf.OlfactometerCalibration(
    input=olf.OlfactometerCalibrationInput(), output=olf.OlfactometerCalibrationOutput()
)

calibration_logic = task_logic.OlfactometerCalibrationLogic(
    task_parameters=task_logic.OlfactometerCalibrationParameters(
        channel_config=channels_config,
        full_flow_rate=1000,
        n_repeats_per_stimulus=10,
        time_on=2,
        time_off=5,
    )
)

calibration_session = AindBehaviorSessionModel(
    root_path="C:\\Data",
    date=utcnow(),
    allow_dirty_repo=False,
    experiment="OlfactometerCalibration",
    experiment_version="0.0.0",
    subject="Olfactometer",
    commit_hash=get_commit_hash(),
)

manipulator_calibration = man.AindManipulatorCalibration(
    output=man.AindManipulatorCalibrationOutput(),
    input=man.AindManipulatorCalibrationInput(
        full_step_to_mm=(man.ManipulatorPosition(x=0.010, y1=0.010, y2=0.010, z=0.010)),
        axis_configuration=[
            man.AxisConfiguration(axis=man.Axis.Y1, min_limit=-0.01, max_limit=25),
            man.AxisConfiguration(axis=man.Axis.Y2, min_limit=-0.01, max_limit=25),
            man.AxisConfiguration(axis=man.Axis.X, min_limit=-0.01, max_limit=25),
            man.AxisConfiguration(axis=man.Axis.Z, min_limit=-0.01, max_limit=25),
        ],
        homing_order=[man.Axis.Y1, man.Axis.Y2, man.Axis.X, man.Axis.Z],
        initial_position=man.ManipulatorPosition(y1=0, y2=0, x=0, z=0),
    ),
)

_rig = rig.OlfactometerCalibrationRig(
    rig_name="OlfactometerRig",
    harp_olfactometer=olf.Olfactometer(port_name="COM10", calibration=calibration),
    harp_analog_input=HarpAnalogInput(port_name="COM8"),
    harp_clock_generator=HarpWhiteRabbit(port_name="COM9"),
    harp_manipulator=man.AindManipulatorDevice(port_name="COM7", calibration=manipulator_calibration),
)


seed_path = "local/olfactometer_{suffix}.json"
os.makedirs(os.path.dirname(seed_path), exist_ok=True)

with open(seed_path.format(suffix="calibration_logic"), "w") as f:
    f.write(calibration_logic.model_dump_json(indent=3))
with open(seed_path.format(suffix="session"), "w") as f:
    f.write(calibration_session.model_dump_json(indent=3))
with open(seed_path.format(suffix="rig"), "w") as f:
    f.write(_rig.model_dump_json(indent=3))

import enum

from aind_behavior_services.rig import olfactometer as abs_olfactometer
from aind_data_schema.components import coordinates, devices


class TrackedDevices(enum.StrEnum):
    """Canonical device names shared by the acquisition and instrument mappers.

    With the exception of the devices that are not part of the rig schema
    (the computer and the photo-ionization detector), names mirror the field
    names of :class:`~aind_behavior_device_olfactometer.rig.OlfactometerCalibrationRig`
    so that both mappers agree on what a device is called.
    """

    COMPUTER = "computer"
    OLFACTOMETER = "harp_olfactometer"
    OLFACTOMETER_EXTENSION = "harp_olfactometer_extension"
    ANALOG_INPUT = "harp_analog_input"
    CLOCK_GENERATOR = "harp_clock_generator"
    MANIPULATOR = "harp_manipulator"
    FLOWMETER = "flowmeter"
    PHOTO_IONIZATION_DETECTOR = "photo_ionization_detector"


#: Subject id AIND uses to mark a data asset as a calibration/test asset. See
#: https://docs.allenneuraldynamics.org/en/latest/acquire_upload/calibration.html
CALIBRATION_SUBJECT_ID = "calibration"

#: Neither Aurora Scientific nor Alicat Scientific exist in ``aind_data_schema_models.organizations``,
#: so both devices are reported with ``Organization.OTHER`` and the real vendor name is carried in
#: ``additional_settings.manufacturer_name``.
PID_MANUFACTURER_NAME = "Aurora Scientific"
PID_MODEL = "200B miniPID"
FLOWMETER_MANUFACTURER_NAME = "Alicat Scientific"
FLOWMETER_MODEL = "M-Series mass flow meter"

#: Analog input channel the photo-ionization detector is wired to. It matches the
#: ``Channel0`` register the data QC reads the PID trace from.
PID_ANALOG_INPUT_CHANNEL = "AnalogInput0"


def olfactometer_extension_name(index: int) -> str:
    """Name of the ``index``-th (1-based) subordinate olfactometer.

    The Bonsai workflow writes these devices out as ``OlfactometerExtension<index>.harp``,
    using the same 1-based ordering as ``OlfactometerCalibrationRig.harp_olfactometer_extension``.
    """
    if index < 1:
        raise ValueError(f"Olfactometer extension index must be 1-based, got {index}.")
    return f"{TrackedDevices.OLFACTOMETER_EXTENSION}_{index}"


def make_origin_coordinate_system() -> coordinates.CoordinateSystem:
    """Coordinate system for the calibration bench.

    Unlike an in vivo rig there is no animal to anchor the origin to, so the
    arbitrary ``Origin.ORIGIN`` is used with plain physical axes.
    """
    return coordinates.CoordinateSystem(
        name="origin",
        origin=coordinates.Origin.ORIGIN,
        axis_unit=coordinates.SizeUnit.MM,
        axes=[
            coordinates.Axis(name=coordinates.AxisName.X, direction=coordinates.Direction.LR),
            coordinates.Axis(name=coordinates.AxisName.Y, direction=coordinates.Direction.FB),
            coordinates.Axis(name=coordinates.AxisName.Z, direction=coordinates.Direction.DU),
        ],
    )


def validate_name(obj: object, name: str) -> str:
    """Return ``name`` if ``obj`` declares a field with that name, else raise.

    Keeps the hard-coded device names honest against the rig schema they mirror.
    """
    if hasattr(obj, name):
        return name
    raise ValueError(f"Model {obj.__class__.__name__} does not contain a field {name}.")


def get_olfactometer_channel(
    ch: abs_olfactometer.OlfactometerChannelConfig,
) -> devices.OlfactometerChannel:
    """Map an ``aind-behavior-services`` olfactometer channel to its aind-data-schema counterpart."""
    ch_type_to_ch_type = {
        abs_olfactometer.OlfactometerChannelType.CARRIER: devices.OlfactometerChannelType.CARRIER,
        abs_olfactometer.OlfactometerChannelType.ODOR: devices.OlfactometerChannelType.ODOR,
    }
    return devices.OlfactometerChannel(
        channel_index=ch.channel_index,
        channel_type=ch_type_to_ch_type[ch.channel_type],
        flow_capacity=ch.flow_rate_capacity,
    )

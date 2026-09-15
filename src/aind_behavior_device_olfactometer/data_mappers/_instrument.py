import dataclasses
import logging
import os
import platform
from pathlib import Path

from aind_behavior_services.rig import olfactometer as abs_olfactometer
from aind_behavior_services.utils import model_from_json_file, utcnow
from aind_data_schema.base import GenericModel
from aind_data_schema.components import connections, devices, measurements
from aind_data_schema.core import instrument
from aind_data_schema_models import modalities
from clabe.data_mapper import aind_data_schema as ads

from ..rig import AlicatFlowmeter, OlfactometerCalibrationRig
from ._utils import (
    FLOWMETER_MANUFACTURER_NAME,
    FLOWMETER_MODEL,
    PID_ANALOG_INPUT_CHANNEL,
    PID_MANUFACTURER_NAME,
    PID_MODEL,
    TrackedDevices,
    get_olfactometer_channel,
    make_origin_coordinate_system,
    olfactometer_extension_name,
    validate_name,
)

logger = logging.getLogger(__name__)


@dataclasses.dataclass(frozen=True)
class _DeviceNode:
    """Helper class to keep track of a device, its connections and the devices it spawns."""

    device_name: str
    device: devices.Device
    connections_from: list[connections.Connection] = dataclasses.field(default_factory=list)
    spawned_devices: list[devices.Device] = dataclasses.field(default_factory=list)


class AindInstrumentDataMapper(ads.AindDataSchemaRigDataMapper):
    """Maps an olfactometer calibration rig schema to an aind-data-schema ``Instrument``."""

    def __init__(
        self,
        data_path: os.PathLike,
    ):
        super().__init__()
        self._data_path = Path(data_path)
        self._mapped: instrument.Instrument | None = None

    def rig_schema(self):
        return self.mapped

    @property
    def session_name(self):
        raise NotImplementedError("Method not implemented.")

    def map(self) -> instrument.Instrument:
        logger.info("Mapping aind-data-schema Instrument.")
        self._mapped = self._map(self._data_path)
        return self.mapped

    @property
    def mapped(self) -> instrument.Instrument:
        if self._mapped is None:
            raise ValueError("Data has not been mapped yet.")
        return self._mapped

    def is_mapped(self) -> bool:
        return self._mapped is not None

    # From here on, private methods only!

    @classmethod
    def _map(cls, root_path: os.PathLike) -> instrument.Instrument:
        rig = read_rig_model(root_path)
        _components, _connections = cls._get_all_components_and_connections(rig)

        computer = next(component for component in _components if isinstance(component, devices.Computer))
        _connections.extend(
            cls._get_connections_from_computer_to_type(
                computer,
                [devices.HarpDevice],
                _components,  # type: ignore [arg-type]
                source_port="USB",
                target_port="USB",
                send_and_receive=True,
            )
        )
        if rig.flowmeter is not None:
            _connections.append(
                connections.Connection(
                    source_device=computer.name,
                    source_port="USB",
                    target_device=TrackedDevices.FLOWMETER,
                    target_port=rig.flowmeter.device_id,
                    send_and_receive=True,
                )
            )

        return instrument.Instrument(
            instrument_id=rig.rig_name,
            modalities=[modalities.Modality.BEHAVIOR],
            modification_date=utcnow().date(),
            coordinate_system=make_origin_coordinate_system(),
            components=_components,  # type: ignore [arg-type]
            connections=_connections,
            calibrations=cls._get_calibrations(rig),
        )

    @staticmethod
    def _get_calibrations(rig: OlfactometerCalibrationRig) -> list[measurements.Calibration]:
        # This workflow acquires the data that a calibration is later fit from; it does
        # not itself produce one. Calibrations already present on the rig schema are
        # emitted by the acquisition mapper instead.
        return []

    @staticmethod
    def _get_connections_from_computer_to_type(
        computer: devices.Computer,
        types: list[type[devices.Device]],
        components: list[devices.Device],
        source_port: str | None = None,
        target_port: str | None = None,
        send_and_receive: bool = True,
    ) -> list[connections.Connection]:
        result_connections = []
        for device in components:
            if any(isinstance(device, device_type) for device_type in types):
                result_connections.append(
                    connections.Connection(
                        source_device=computer.name,
                        target_device=device.name,
                        source_port=source_port,
                        target_port=target_port,
                        send_and_receive=send_and_receive,
                    )
                )
        return result_connections

    @staticmethod
    def _get_computer(rig: OlfactometerCalibrationRig) -> devices.Computer:
        return devices.Computer(
            name=TrackedDevices.COMPUTER,
            manufacturer=devices.Organization.AIND,
            operating_system=platform.platform(),
            serial_number=rig.computer_name,
        )

    @staticmethod
    def _get_olfactometer(name: str, device: abs_olfactometer.Olfactometer) -> devices.Olfactometer:
        return devices.Olfactometer(
            name=name,
            harp_device_type=devices.HarpDeviceType.OLFACTOMETER,
            manufacturer=devices.Organization.CHAMPALIMAUD,
            is_clock_generator=False,
            channels=list(map(get_olfactometer_channel, device.calibration.channel_config.values())),
        )

    @classmethod
    def _get_olfactometers(cls, rig: OlfactometerCalibrationRig) -> list[devices.Olfactometer]:
        olfactometers = [cls._get_olfactometer(validate_name(rig, TrackedDevices.OLFACTOMETER), rig.harp_olfactometer)]
        for index, extension in enumerate(rig.harp_olfactometer_extension, start=1):
            olfactometers.append(cls._get_olfactometer(olfactometer_extension_name(index), extension))
        return olfactometers

    @staticmethod
    def _get_analog_input_node(rig: OlfactometerCalibrationRig) -> _DeviceNode:
        """The Harp analog input board and the photo-ionization detector it digitizes.

        The PID is not part of the rig schema, but the calibration is meaningless
        without it and the data QC reads its trace from ``AnalogData/Channel0``.
        """
        source_device = validate_name(rig, TrackedDevices.ANALOG_INPUT)

        photo_ionization_detector = get_photo_ionization_detector()

        _connections = [
            connections.Connection(
                source_device=TrackedDevices.PHOTO_IONIZATION_DETECTOR,
                target_device=source_device,
                target_port=PID_ANALOG_INPUT_CHANNEL,
            )
        ]

        harp_device = devices.HarpDevice(
            name=source_device,
            harp_device_type=devices.HarpDeviceType.ANALOGINPUT,
            is_clock_generator=False,
            channels=[
                devices.DAQChannel(
                    channel_name=PID_ANALOG_INPUT_CHANNEL,
                    channel_type=devices.DaqChannelType.AI,
                )
            ],
        )

        return _DeviceNode(
            device_name=source_device,
            device=harp_device,
            connections_from=_connections,
            spawned_devices=[photo_ionization_detector],
        )

    @staticmethod
    def _get_manipulator(rig: OlfactometerCalibrationRig) -> devices.HarpDevice:
        return devices.HarpDevice(
            name=validate_name(rig, TrackedDevices.MANIPULATOR),
            harp_device_type=devices.HarpDeviceType.STEPPERDRIVER,
            manufacturer=devices.Organization.OEPS,
            is_clock_generator=False,
            notes="Positions the odor delivery tube relative to the photo-ionization detector.",
        )

    @staticmethod
    def _get_clock_generator_node(rig: OlfactometerCalibrationRig, components: list[devices.Device]) -> _DeviceNode:
        source_device = validate_name(rig, TrackedDevices.CLOCK_GENERATOR)

        harp_devices = [d for d in components if isinstance(d, devices.HarpDevice)]
        _connections = [
            connections.Connection(
                source_device=source_device,
                target_device=device.name,
                source_port="ClkOut",
                target_port="ClkIn",
            )
            for device in harp_devices
            if device.name != source_device
        ]

        harp_device = devices.HarpDevice(
            name=source_device,
            harp_device_type=devices.HarpDeviceType.WHITERABBIT,
            manufacturer=devices.Organization.AIND,
            is_clock_generator=True,
            channels=[
                devices.DAQChannel(channel_name="ClkOut", channel_type=devices.DaqChannelType.DO),
            ],
        )

        return _DeviceNode(device_name=source_device, device=harp_device, connections_from=_connections)

    @classmethod
    def _get_all_components_and_connections(
        cls, rig: OlfactometerCalibrationRig
    ) -> tuple[list[devices.DataModel], list[connections.Connection]]:
        _components: list[devices.DataModel] = []
        _connections: list[connections.Connection] = []

        _components.append(cls._get_computer(rig))
        _components.extend(cls._get_olfactometers(rig))

        analog_input_node = cls._get_analog_input_node(rig)
        _components.append(analog_input_node.device)
        _components.extend(analog_input_node.spawned_devices)
        _connections.extend(analog_input_node.connections_from)

        _components.append(cls._get_manipulator(rig))

        if rig.flowmeter is not None:
            _components.append(get_flowmeter(rig.flowmeter))

        # Leave the clock for last so that it binds to every other Harp device
        clock_generator_node = cls._get_clock_generator_node(rig, _components)  # type: ignore [arg-type]
        _components.append(clock_generator_node.device)
        _connections.extend(clock_generator_node.connections_from)

        return _components, _connections


def get_photo_ionization_detector() -> devices.Device:
    """The PID that measures the odor delivered by the olfactometer.

    The PID is not part of the rig schema, but the calibration is meaningless without
    it and the data QC reads its trace from ``AnalogData/Channel0``. It is also the
    calibration object the acquisition is performed against, so the subject mapper
    reports it too.

    Specifications are from the Aurora Scientific 200B miniPID datasheet:
    https://aurorascientific.com/products/neuroscience/200b-minipid/
    """
    return devices.Device(
        name=TrackedDevices.PHOTO_IONIZATION_DETECTOR,
        manufacturer=devices.Organization.OTHER,
        model=PID_MODEL,
        additional_settings=GenericModel.model_validate(
            {
                "manufacturer_name": PID_MANUFACTURER_NAME,
                "datasheet": "https://aurorascientific.com/products/neuroscience/200b-minipid/",
            }
        ),
        notes=(
            f"{PID_MANUFACTURER_NAME} {PID_MODEL} photo-ionization detector, used to measure the odor "
            "concentration at the output of the olfactometer. The sensor head contains the detection "
            "cell, electrometer and RF-excited UV lamp; the controller sets pump speed, gain and zero, "
            "and exposes a 0-10 V analog output. That output is digitized by the Harp analog input "
            f"board on {PID_ANALOG_INPUT_CHANNEL}."
        ),
    )


def get_flowmeter(flowmeter: AlicatFlowmeter) -> devices.Device:
    """The Alicat mass flow meter used as an independent flow-rate reference.

    Specifications are from the Alicat M/MB-Series mid-flow datasheet
    (DOC-SPECS-M-MID, rev 6): https://documents.alicat.com/specifications/DOC-SPECS-M-MID.pdf
    """
    return devices.Device(
        name=TrackedDevices.FLOWMETER,
        manufacturer=devices.Organization.OTHER,
        model=FLOWMETER_MODEL,
        additional_settings=GenericModel.model_validate(
            {
                "manufacturer_name": FLOWMETER_MANUFACTURER_NAME,
                "datasheet": "https://documents.alicat.com/specifications/DOC-SPECS-M-MID.pdf",
                "configuration": flowmeter.model_dump(mode="json"),
            }
        ),
        notes=(
            f"{FLOWMETER_MANUFACTURER_NAME} {FLOWMETER_MODEL} used as an independent reference for the "
            "flow rates reported by the olfactometer. Read over a serial connection as device "
            f"{flowmeter.device_id!r} and polled every {flowmeter.pooling_period} s."
        ),
    )


def read_rig_model(root_path: os.PathLike) -> OlfactometerCalibrationRig:
    """Load the rig schema the Bonsai workflow was launched with."""
    return model_from_json_file(Path(root_path) / "Behavior" / "Logs" / "rig_input.json", OlfactometerCalibrationRig)


def get_component_names(rig: OlfactometerCalibrationRig) -> list[str]:
    """Names of every device the instrument mapper emits for ``rig``.

    The acquisition mapper uses this so that ``DataStream.active_devices`` is
    guaranteed to resolve against ``Instrument.components``.
    """
    components, _ = AindInstrumentDataMapper._get_all_components_and_connections(rig)
    return [component.name for component in components]

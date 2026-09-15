"""Tests for the aind-data-schema data mappers.

The mappers need aind-data-schema, clabe and GitPython. These come from the ``data-mappers``
extra, which the ``dev`` dependency group pulls in, so ``uv sync`` installs them and these
tests run by default. They stay guarded so that a bare install of this package -- without the
extra -- skips instead of failing to import.
"""

import importlib.util
import json
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

from aind_behavior_services.rig import aind_manipulator as man
from aind_behavior_services.rig import olfactometer as olf
from aind_behavior_services.rig.harp import HarpAnalogInput, HarpWhiteRabbit
from aind_behavior_services.session import Session

from aind_behavior_device_olfactometer import rig as rig_module
from aind_behavior_device_olfactometer import task_logic as task_logic_module

_HAS_DATA_MAPPERS = all(importlib.util.find_spec(module) is not None for module in ("aind_data_schema", "clabe", "git"))
_SKIP_REASON = (
    "aind-data-schema/clabe/GitPython are not installed, so the data mappers cannot be imported. "
    "Install the 'data-mappers' extra (`uv sync` does this by default)."
)

MOCK_SESSION_START_TIME = datetime(2023, 1, 1, 11, 0, 0, tzinfo=UTC)
MOCK_SESSION_END_TIME = datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC)


def _make_rig() -> rig_module.OlfactometerCalibrationRig:
    olf_calibration = olf.OlfactometerCalibration(
        channel_config={
            olf.OlfactometerChannel.Channel0: olf.OlfactometerChannelConfig(
                channel_index=olf.OlfactometerChannel.Channel0,
                channel_type=olf.OlfactometerChannelType.ODOR,
                flow_rate=100,
                odorant="Banana",
                odorant_dilution=0.1,
            ),
            olf.OlfactometerChannel.Channel1: olf.OlfactometerChannelConfig(
                channel_index=olf.OlfactometerChannel.Channel1,
                channel_type=olf.OlfactometerChannelType.ODOR,
                flow_rate=100,
                odorant="Vanilla",
                odorant_dilution=0.05,
            ),
            # Deliberately missing a dilution: the mapper must skip it rather than fail.
            olf.OlfactometerChannel.Channel2: olf.OlfactometerChannelConfig(
                channel_index=olf.OlfactometerChannel.Channel2,
                channel_type=olf.OlfactometerChannelType.ODOR,
                flow_rate=100,
                odorant="Amyl acetate",
            ),
            olf.OlfactometerChannel.Channel3: olf.OlfactometerChannelConfig(
                channel_index=olf.OlfactometerChannel.Channel3,
                channel_type=olf.OlfactometerChannelType.CARRIER,
                odorant="Air",
                flow_rate_capacity=1000,
            ),
        }
    )

    extension_calibration = olf_calibration.model_copy(deep=True)
    extension_calibration.channel_config[olf.OlfactometerChannel.Channel3] = olf.OlfactometerChannelConfig(
        channel_index=olf.OlfactometerChannel.Channel3,
        channel_type=olf.OlfactometerChannelType.ODOR,
        flow_rate=100,
        odorant="Eucalyptus",
        odorant_dilution=0.2,
    )

    manipulator_calibration = man.AindManipulatorCalibration(
        full_step_to_mm=man.ManipulatorPosition(x=0.010, y1=0.010, y2=0.010, z=0.010),
        axis_configuration=[
            man.AxisConfiguration(axis=man.Axis.Y1, min_limit=-0.01, max_limit=25),
            man.AxisConfiguration(axis=man.Axis.Y2, min_limit=-0.01, max_limit=25),
            man.AxisConfiguration(axis=man.Axis.X, min_limit=-0.01, max_limit=25),
            man.AxisConfiguration(axis=man.Axis.Z, min_limit=-0.01, max_limit=25),
        ],
        homing_order=[man.Axis.Y1, man.Axis.Y2, man.Axis.X, man.Axis.Z],
        initial_position=man.ManipulatorPosition(y1=0, y2=0, x=0, z=0),
    )

    return rig_module.OlfactometerCalibrationRig(
        computer_name="TestPC",
        data_directory=r"C:/data",
        rig_name="OlfactometerRig",
        harp_olfactometer=olf.Olfactometer(port_name="COM10", calibration=olf_calibration),
        harp_olfactometer_extension=[olf.Olfactometer(port_name="COM11", calibration=extension_calibration)],
        harp_analog_input=HarpAnalogInput(port_name="COM8"),
        harp_clock_generator=HarpWhiteRabbit(port_name="COM9"),
        harp_manipulator=man.AindManipulator(port_name="COM7", calibration=manipulator_calibration),
        flowmeter=rig_module.AlicatFlowmeter(port_name="COM6", device_id="A", pooling_period=0.2),
    )


def _make_session() -> Session:
    return Session(
        date=MOCK_SESSION_START_TIME,
        allow_dirty_repo=True,
        experiment="OlfactometerCalibration",
        subject="CALIBRATION",
        experimenter=["A. Scientist"],
        notes="Session for OlfactometerCalibration. No animal is being run.",
    )


def _make_task_logic() -> task_logic_module.OlfactometerCalibrationLogic:
    return task_logic_module.OlfactometerCalibrationLogic(
        task_parameters=task_logic_module.OlfactometerCalibrationParameters(
            full_flow_rate=1000,
            n_repeats_per_stimulus=10,
            time_on=2,
            time_off=5,
        )
    )


@unittest.skipUnless(_HAS_DATA_MAPPERS, _SKIP_REASON)
class TestAindDataMappers(unittest.TestCase):
    def setUp(self):
        from aind_behavior_device_olfactometer.data_mappers._acquisition import AindAcquisitionDataMapper
        from aind_behavior_device_olfactometer.data_mappers._instrument import AindInstrumentDataMapper

        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_path = Path(self.temp_dir.name)

        logs_dir = self.data_path / "Behavior" / "Logs"
        logs_dir.mkdir(parents=True, exist_ok=True)

        with open(logs_dir / "session_input.json", "w", encoding="utf-8") as f:
            json.dump(_make_session().model_dump(mode="json"), f, indent=2)
        with open(logs_dir / "rig_input.json", "w", encoding="utf-8") as f:
            json.dump(_make_rig().model_dump(mode="json"), f, indent=2)
        with open(logs_dir / "tasklogic_input.json", "w", encoding="utf-8") as f:
            json.dump(_make_task_logic().model_dump(mode="json"), f, indent=2)

        self.repo_path = Path("./")
        self.session_start_time = MOCK_SESSION_START_TIME
        self.session_end_time = MOCK_SESSION_END_TIME

        self.session_mapper = AindAcquisitionDataMapper(
            data_path=self.data_path,
            repository_path=self.repo_path,
            session_end_time=self.session_end_time,
        )
        self.rig_mapper = AindInstrumentDataMapper(data_path=self.data_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_session_mock_map(self):
        with patch(
            "aind_behavior_device_olfactometer.data_mappers._acquisition.AindAcquisitionDataMapper._map"
        ) as mock_map:
            mock_map.return_value = MagicMock()
            result = self.session_mapper.map()
        self.assertIsNotNone(result)
        self.assertTrue(self.session_mapper.is_mapped())

    def test_session_map(self):
        self.assertIsNotNone(self.session_mapper.map())

    def test_session_round_trip(self):
        from aind_data_schema.core import acquisition

        mapped = self.session_mapper.map()
        acquisition.Acquisition.model_validate_json(mapped.model_dump_json())

    def test_acquisition_bounds_come_from_session_and_argument(self):
        mapped = self.session_mapper.map()

        self.assertEqual(mapped.acquisition_start_time, self.session_start_time)
        self.assertEqual(mapped.acquisition_end_time, self.session_end_time)

        stream = mapped.data_streams[0]
        self.assertEqual(stream.stream_start_time, self.session_start_time)
        self.assertEqual(stream.stream_end_time, self.session_end_time)

        epoch = mapped.stimulus_epochs[0]
        self.assertEqual(epoch.stimulus_start_time, self.session_start_time)
        self.assertEqual(epoch.stimulus_end_time, self.session_end_time)

    def test_acquisition_has_no_subject_details(self):
        """No animal takes part in a calibration."""
        self.assertIsNone(self.session_mapper.map().subject_details)

    def test_acquisition_uses_the_calibration_subject_id(self):
        """AIND marks calibration assets with subject_id="calibration"."""
        self.assertEqual(self.session_mapper.map().subject_id, "calibration")

    def test_stimulus_epoch_lists_every_olfactometer(self):
        from aind_behavior_device_olfactometer.data_mappers._utils import TrackedDevices

        epoch = self.session_mapper.map().stimulus_epochs[0]
        self.assertEqual(
            epoch.active_devices,
            [str(TrackedDevices.OLFACTOMETER), f"{TrackedDevices.OLFACTOMETER_EXTENSION}_1"],
        )
        self.assertEqual(len(epoch.configurations), 2)

    def test_stimulus_epoch_skips_channels_without_odorant_metadata(self):
        """Carrier channels and odor channels missing a dilution are not reported."""
        epoch = self.session_mapper.map().stimulus_epochs[0]
        main_config = epoch.configurations[0]
        self.assertEqual([c.odorant for c in main_config.channel_configs], ["Banana", "Vanilla"])

        extension_config = epoch.configurations[1]
        self.assertEqual([c.odorant for c in extension_config.channel_configs], ["Banana", "Vanilla", "Eucalyptus"])

    def test_session_end_time_before_start_time_raises(self):
        from aind_behavior_device_olfactometer.data_mappers._acquisition import AindAcquisitionDataMapper

        mapper = AindAcquisitionDataMapper(
            data_path=self.data_path,
            repository_path=self.repo_path,
            session_end_time=self.session_start_time - (self.session_end_time - self.session_start_time),
        )
        with self.assertRaises(ValueError):
            mapper.map()

    def test_rig_mock_map(self):
        with patch(
            "aind_behavior_device_olfactometer.data_mappers._instrument.AindInstrumentDataMapper._map"
        ) as mock_map:
            mock_map.return_value = MagicMock()
            result = self.rig_mapper.map()
        self.assertIsNotNone(result)
        self.assertTrue(self.rig_mapper.is_mapped())

    def test_rig_map(self):
        self.assertIsNotNone(self.rig_mapper.map())

    def test_rig_round_trip(self):
        from aind_data_schema.core import instrument

        mapped = self.rig_mapper.map()
        instrument.Instrument.model_validate_json(mapped.model_dump_json())

    def test_rig_includes_olfactometer_extensions(self):
        from aind_data_schema.components import devices

        mapped = self.rig_mapper.map()
        olfactometers = [c.name for c in mapped.components if isinstance(c, devices.Olfactometer)]
        self.assertEqual(olfactometers, ["harp_olfactometer", "harp_olfactometer_extension_1"])

    def test_rig_clock_generator_drives_every_harp_device(self):
        from aind_data_schema.components import devices

        mapped = self.rig_mapper.map()
        harp_names = {c.name for c in mapped.components if isinstance(c, devices.HarpDevice)}
        clocked = {
            connection.target_device
            for connection in mapped.connections
            if connection.source_device == "harp_clock_generator"
        }
        self.assertEqual(clocked, harp_names - {"harp_clock_generator"})

    def test_rig_photo_ionization_detector_details(self):
        """The PID carries its datasheet identity even though it is not in the rig schema."""
        mapped = self.rig_mapper.map()
        pid = next(c for c in mapped.components if c.name == "photo_ionization_detector")

        self.assertEqual(pid.model, "200B miniPID")
        # Aurora Scientific is not in aind_data_schema_models.organizations, so the real
        # vendor has to travel in additional_settings alongside Organization.OTHER.
        self.assertEqual(pid.manufacturer.name, "Other")
        settings = pid.additional_settings.model_dump()
        self.assertEqual(settings["manufacturer_name"], "Aurora Scientific")
        self.assertEqual(
            settings["datasheet"],
            "https://aurorascientific.com/products/neuroscience/200b-minipid/",
        )
        self.assertIn("AnalogInput0", pid.notes)

    def test_rig_flowmeter_details(self):
        """The flowmeter carries its datasheet identity plus the rig-side serial settings."""
        mapped = self.rig_mapper.map()
        flowmeter = next(c for c in mapped.components if c.name == "flowmeter")

        self.assertEqual(flowmeter.model, "M-Series mass flow meter")
        self.assertEqual(flowmeter.manufacturer.name, "Other")
        settings = flowmeter.additional_settings.model_dump()
        self.assertEqual(settings["manufacturer_name"], "Alicat Scientific")
        self.assertEqual(
            settings["datasheet"],
            "https://documents.alicat.com/specifications/DOC-SPECS-M-MID.pdf",
        )
        self.assertEqual(settings["configuration"]["device_id"], "A")
        self.assertEqual(settings["configuration"]["port_name"], "COM6")
        self.assertEqual(settings["configuration"]["pooling_period"], 0.2)

    def test_rig_omits_flowmeter_when_absent(self):
        rig = _make_rig()
        rig.flowmeter = None
        with open(self.data_path / "Behavior" / "Logs" / "rig_input.json", "w", encoding="utf-8") as f:
            json.dump(rig.model_dump(mode="json"), f, indent=2)

        mapped = self.rig_mapper.map()
        self.assertNotIn("flowmeter", [c.name for c in mapped.components])

    def test_instrument_acquisition_compatibility(self):
        from aind_data_schema.utils import compatibility_check

        session_mapped = self.session_mapper.map()
        rig_mapped = self.rig_mapper.map()
        compatibility_check.InstrumentAcquisitionCompatibility(
            instrument=rig_mapped, acquisition=session_mapped
        ).run_compatibility_check(raise_for_missing_devices=True)

    def test_subject_map(self):
        from aind_behavior_device_olfactometer.data_mappers._subject import AindSubjectDataMapper

        mapped = AindSubjectDataMapper(data_path=self.data_path).map()
        self.assertEqual(mapped.subject_id, "calibration")
        self.assertFalse(mapped.subject_details.empty)
        self.assertEqual(
            [o.name for o in mapped.subject_details.objects],
            ["photo_ionization_detector"],
        )

    def test_subject_round_trip(self):
        from aind_data_schema.core import subject

        from aind_behavior_device_olfactometer.data_mappers._subject import AindSubjectDataMapper

        mapped = AindSubjectDataMapper(data_path=self.data_path).map()
        subject.Subject.model_validate_json(mapped.model_dump_json())

    def test_subject_and_acquisition_agree(self):
        from aind_behavior_device_olfactometer.data_mappers._subject import AindSubjectDataMapper

        self.assertEqual(
            AindSubjectDataMapper(data_path=self.data_path).map().subject_id,
            self.session_mapper.map().subject_id,
        )

    def _map_dataset(self, **kwargs):
        from aind_behavior_device_olfactometer.data_mappers import map_dataset

        return map_dataset(
            self.data_path,
            self.repo_path,
            session_end_time=self.session_end_time,
            **kwargs,
        )

    def test_map_dataset_syncs_the_instrument_id(self):
        mapped = self._map_dataset()
        self.assertEqual(mapped.acquisition.instrument_id, mapped.instrument.instrument_id)
        self.assertIsNotNone(mapped.subject)

    def test_map_dataset_can_skip_the_subject(self):
        self.assertIsNone(self._map_dataset(map_subject=False).subject)

    def test_write_standard_files(self):
        written = self._map_dataset().write_standard_files(self.data_path)

        self.assertEqual(
            sorted(path.name for path in written),
            ["acquisition_olfactometer.json", "instrument_olfactometer.json", "subject_olfactometer.json"],
        )
        for path in written:
            self.assertTrue(path.exists(), f"{path} was reported as written but does not exist")

    def test_write_standard_files_without_a_suffix(self):
        written = self._map_dataset(map_subject=False).write_standard_files(self.data_path, filename_suffix=None)

        self.assertEqual(
            sorted(path.name for path in written),
            ["acquisition.json", "instrument.json"],
        )
        for path in written:
            self.assertTrue(path.exists(), f"{path} was reported as written but does not exist")


if __name__ == "__main__":
    unittest.main()

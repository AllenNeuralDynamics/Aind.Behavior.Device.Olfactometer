import datetime
import json
import logging
import os
import sys
from functools import cached_property
from pathlib import Path

import git
import pydantic
from aind_behavior_services.rig import olfactometer as abs_olfactometer
from aind_behavior_services.session import Session
from aind_behavior_services.utils import model_from_json_file
from aind_data_schema.components import configs
from aind_data_schema.core import acquisition
from aind_data_schema_models.modalities import Modality
from clabe.apps import BonsaiApp
from clabe.data_mapper import aind_data_schema as ads
from clabe.data_mapper import helpers as data_mapper_helpers
from pydantic import AwareDatetime

from .. import __semver__
from ..rig import OlfactometerCalibrationRig
from ..task_logic import OlfactometerCalibrationLogic
from ._instrument import get_component_names
from ._utils import CALIBRATION_SUBJECT_ID, TrackedDevices, olfactometer_extension_name

logger = logging.getLogger(__name__)


class AindAcquisitionDataMapper(ads.AindDataSchemaSessionDataMapper):
    """Maps an olfactometer calibration dataset to an aind-data-schema ``Acquisition``."""

    def __init__(
        self,
        data_path: os.PathLike,
        repository_path: os.PathLike,
        session_end_time: AwareDatetime,
    ):
        self._data_path = Path(data_path)
        self._repository_path = Path(repository_path)
        self.session_end_time = session_end_time

        abs_schemas_path = self._data_path / "Behavior" / "Logs"
        self.session_model = model_from_json_file(abs_schemas_path / "session_input.json", Session)
        self.rig_model = model_from_json_file(abs_schemas_path / "rig_input.json", OlfactometerCalibrationRig)
        self.task_model = model_from_json_file(abs_schemas_path / "tasklogic_input.json", OlfactometerCalibrationLogic)

        self.repository = git.Repo(self._repository_path)
        assert self.repository.working_tree_dir is not None
        self.bonsai_app = BonsaiApp(
            executable=Path(self.repository.working_tree_dir) / ".bonsai" / "Bonsai.exe",
            workflow=Path(self.repository.working_tree_dir) / "src" / "main.bonsai",
        )

        self._mapped: acquisition.Acquisition | None = None

    def session_schema(self):
        return self.mapped

    @property
    def session_name(self) -> str:
        if self.session_model.session_name is None:
            raise ValueError("Session name is not set in the session model.")
        return self.session_model.session_name

    @property
    def mapped(self) -> acquisition.Acquisition:
        if self._mapped is None:
            raise ValueError("Data has not been mapped yet.")
        return self._mapped

    def is_mapped(self) -> bool:
        return self._mapped is not None

    def map(self) -> acquisition.Acquisition:
        logger.info("Mapping aind-data-schema Acquisition.")
        try:
            self._mapped = self._map()
        except (OSError, pydantic.ValidationError, ValueError) as e:
            logger.error("Failed to map to aind-data-schema Acquisition. %s", e)
            raise
        else:
            return self._mapped

    def _map(self) -> acquisition.Acquisition:
        return acquisition.Acquisition(
            subject_id=self._subject_id(),
            # No animal takes part in a calibration, so subject_details is deliberately omitted.
            subject_details=None,
            instrument_id=self.rig_model.rig_name,
            acquisition_start_time=self.session_model.date,
            acquisition_end_time=self.session_end_time,
            experimenters=self.session_model.experimenter,
            acquisition_type=self.task_model.name,
            coordinate_system=None,
            data_streams=self._get_data_streams(),
            calibrations=[],
            stimulus_epochs=self._get_stimulus_epochs(),
            notes=self._get_notes(),
        )

    def _subject_id(self) -> str:
        """AIND marks calibration data assets with ``subject_id="calibration"``.

        See https://docs.allenneuraldynamics.org/en/latest/acquire_upload/calibration.html
        """
        if self.session_model.subject.casefold() != CALIBRATION_SUBJECT_ID:
            logger.warning(
                "Session subject is %r, but this workflow only ever calibrates hardware. Reporting %r instead.",
                self.session_model.subject,
                CALIBRATION_SUBJECT_ID,
            )
        return CALIBRATION_SUBJECT_ID

    @cached_property
    def _stream_bound_times(self) -> tuple[datetime.datetime, datetime.datetime]:
        """Start and end times of the acquisition.

        The olfactometer workflow does not log a wall-clock start/end event (its
        ``EndSession`` event only carries a Harp timestamp), so the session schema
        supplies the start and the caller supplies the end.
        """
        start_time = self.session_model.date
        end_time = self.session_end_time
        if end_time < start_time:
            raise ValueError(
                f"Session end time {end_time.isoformat()} precedes the session start time {start_time.isoformat()}."
            )
        return start_time, end_time

    def _get_notes(self) -> str | None:
        parts = [p for p in [self.session_model.notes, self._end_session_notes()] if p]
        return "\n".join(parts) if parts else None

    def _end_session_notes(self) -> str | None:
        """Flag sessions whose ``EndSession`` event is missing, i.e. that did not close cleanly."""
        end_session_path = self._data_path / "behavior" / "SoftwareEvents" / "EndSession.json"
        if not end_session_path.exists():
            return "No EndSession event was found; the workflow may not have terminated cleanly."
        lines = [line for line in end_session_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if not lines:
            return "The EndSession event file is empty; the workflow may not have terminated cleanly."
        try:
            json.loads(lines[-1])
        except json.JSONDecodeError:
            return "The EndSession event could not be parsed; the workflow may not have terminated cleanly."
        return None

    def _get_data_streams(self) -> list[acquisition.DataStream]:
        stream_start_time, stream_end_time = self._stream_bound_times
        return [
            acquisition.DataStream(
                stream_start_time=stream_start_time,
                stream_end_time=stream_end_time,
                code=[self._get_bonsai_as_code(), self._get_python_as_code()],
                active_devices=get_component_names(self.rig_model),
                modalities=[Modality.BEHAVIOR],
                configurations=[],
            )
        ]

    def _get_stimulus_epochs(self) -> list[acquisition.StimulusEpoch]:
        active_devices: list[str] = []
        stimulus_epoch_configurations: list[configs.OlfactometerConfig] = []

        for device_name, device in self._olfactometers():
            active_devices.append(device_name)
            stimulus_epoch_configurations.append(
                configs.OlfactometerConfig(
                    device_name=device_name,
                    channel_configs=_get_olfactometer_channel_info(device_name, device),
                )
            )

        # Note: According to this discussion, if stimuli are programmatically generated, we can use this instead of
        # configuration. https://github.com/AllenNeuralDynamics/aind-data-schema/discussions/1550#discussioncomment-14246854
        _stim_code = self._get_bonsai_as_code()
        _stim_code.parameters = acquisition.GenericModel.model_validate(
            {
                "task_logic": "./Behavior/Logs/tasklogic_input.json",
                "rig": "./Behavior/Logs/rig_input.json",
                "session": "./Behavior/Logs/session_input.json",
            }
        )

        start_time, end_time = self._stream_bound_times
        return [
            acquisition.StimulusEpoch(
                active_devices=active_devices,
                code=_stim_code,
                stimulus_start_time=start_time,
                stimulus_end_time=end_time,
                configurations=stimulus_epoch_configurations,
                stimulus_name=self.task_model.name,
                stimulus_modalities=[acquisition.StimulusModality.OLFACTORY],
                notes=(
                    "Odors are delivered to a photo-ionization detector rather than to an animal; "
                    "this epoch describes the odors that were presented during the calibration."
                ),
            )
        ]

    def _olfactometers(self) -> list[tuple[str, abs_olfactometer.Olfactometer]]:
        """Every olfactometer in the rig, paired with the name the instrument mapper gives it."""
        olfactometers = [(str(TrackedDevices.OLFACTOMETER), self.rig_model.harp_olfactometer)]
        for index, extension in enumerate(self.rig_model.harp_olfactometer_extension, start=1):
            olfactometers.append((olfactometer_extension_name(index), extension))
        return olfactometers

    def _get_bonsai_as_code(self) -> acquisition.Code:
        assert isinstance(self.repository, git.Repo)
        return acquisition.Code(
            url=self.repository.remote().url,
            name="Aind.Behavior.Device.Olfactometer",
            version=__semver__,
            commit_hash=self.repository.head.commit.hexsha,
            language="Bonsai",
            language_version=self._bonsai_version(),
            run_script=Path(self.bonsai_app.workflow),
        )

    def _bonsai_version(self) -> str:
        bonsai_config = Path(self.bonsai_app.executable).parent / "Bonsai.config"
        try:
            return data_mapper_helpers.snapshot_bonsai_environment(bonsai_config).get("Bonsai", "unknown")
        except (OSError, ValueError) as e:
            logger.warning("Could not read the Bonsai environment from %s: %s", bonsai_config, e)
            return "unknown"

    def _get_python_as_code(self) -> acquisition.Code:
        assert isinstance(self.repository, git.Repo)
        v = sys.version_info
        semver = f"{v.major}.{v.minor}.{v.micro}"
        if v.releaselevel != "final":
            semver += f"-{v.releaselevel}.{v.serial}"
        return acquisition.Code(
            url=self.repository.remote().url,
            name="aind-behavior-device-olfactometer",
            version=__semver__,
            commit_hash=self.repository.head.commit.hexsha,
            language="Python",
            language_version=semver,
        )


def _get_olfactometer_channel_info(
    device_name: str, device: abs_olfactometer.Olfactometer
) -> list[configs.OlfactometerChannelInfo]:
    channel_info: list[configs.OlfactometerChannelInfo] = []
    for channel in device.calibration.channel_config.values():
        if channel.channel_type != abs_olfactometer.OlfactometerChannelType.ODOR:
            continue
        # odorant and dilution are both required by the aind-data-schema model.
        if channel.odorant is None or channel.odorant_dilution is None:
            logger.warning(
                "Channel %d of %s is configured as ODOR but odorant or dilution is not set. Skipping this channel.",
                channel.channel_index,
                device_name,
            )
            continue
        channel_info.append(
            configs.OlfactometerChannelInfo(
                channel_index=channel.channel_index,
                odorant=channel.odorant,
                dilution=channel.odorant_dilution,
            )
        )
    return channel_info

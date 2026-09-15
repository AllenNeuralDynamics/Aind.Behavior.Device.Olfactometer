"""Map an olfactometer calibration dataset to aind-data-schema metadata.

This subpackage is imported directly from Python; it is deliberately not exposed through
``device-olfactometer``. It needs ``aind-data-schema``, ``aind-clabe[aind-services]`` and
``GitPython``, which are not dependencies of this package (see the README).

Typical use:

    from aind_behavior_device_olfactometer.data_mappers import map_dataset

    mapped = map_dataset(session_directory, repository_path, session_end_time=utcnow())
    mapped.write_standard_files(session_directory)
"""

import dataclasses
import logging
import os
from pathlib import Path

from aind_data_schema.core.acquisition import Acquisition
from aind_data_schema.core.instrument import Instrument
from aind_data_schema.core.subject import Subject
from pydantic import AwareDatetime

from ._acquisition import AindAcquisitionDataMapper
from ._instrument import AindInstrumentDataMapper
from ._subject import AindSubjectDataMapper

logger = logging.getLogger(__name__)

DEFAULT_FILENAME_SUFFIX = "olfactometer"

__all__ = [
    "AindAcquisitionDataMapper",
    "AindInstrumentDataMapper",
    "AindSubjectDataMapper",
    "MappedMetadata",
    "map_dataset",
]


@dataclasses.dataclass(frozen=True)
class MappedMetadata:
    """The aind-data-schema models mapped from a single calibration dataset."""

    acquisition: Acquisition
    instrument: Instrument
    subject: Subject | None = None

    def write_standard_files(
        self,
        output_directory: os.PathLike,
        filename_suffix: str | None = DEFAULT_FILENAME_SUFFIX,
    ) -> list[Path]:
        """Write each mapped model to ``output_directory`` and return the files written."""
        output_directory = Path(output_directory)
        written: list[Path] = []
        for model in (self.acquisition, self.instrument, self.subject):
            if model is None:
                continue
            model.write_standard_file(output_directory=output_directory, filename_suffix=filename_suffix)
            written.append(output_directory / _standard_filename(model, filename_suffix))
        logger.info("Wrote %s", ", ".join(path.name for path in written))
        return written


def map_dataset(
    data_path: os.PathLike,
    repository_path: os.PathLike,
    session_end_time: AwareDatetime,
    *,
    map_subject: bool = True,
) -> MappedMetadata:
    """Map the calibration dataset at ``data_path`` to aind-data-schema metadata.

    Args:
        data_path: The session directory the Bonsai workflow wrote to.
        repository_path: The ``Aind.Behavior.Device.Olfactometer`` checkout the workflow ran from.
        session_end_time: The olfactometer workflow does not log a wall-clock end time, so the
            caller must supply one.
        map_subject: Also map a ``Subject`` describing the calibration object that stands in for
            the animal. Set to False when something else (e.g. ``aind-metadata-mapper``) generates
            it during upload.
    """
    data_path = Path(data_path)

    acquisition_mapper = AindAcquisitionDataMapper(
        data_path=data_path,
        repository_path=Path(repository_path),
        session_end_time=session_end_time,
    )
    acquisition_mapper.map()

    instrument_mapper = AindInstrumentDataMapper(data_path=data_path)
    instrument_mapper.map()

    acquisition_mapper.mapped.instrument_id = instrument_mapper.mapped.instrument_id

    mapped_subject = AindSubjectDataMapper(data_path=data_path).map() if map_subject else None

    return MappedMetadata(
        acquisition=acquisition_mapper.mapped,
        instrument=instrument_mapper.mapped,
        subject=mapped_subject,
    )


def _standard_filename(model: Acquisition | Instrument | Subject, filename_suffix: str | None) -> str:
    """Reproduce the filename ``write_standard_file`` picks for ``model``."""
    filename = Path(model.default_filename())
    if not filename_suffix:
        return filename.name
    return f"{filename.stem}_{filename_suffix}{filename.suffix}"

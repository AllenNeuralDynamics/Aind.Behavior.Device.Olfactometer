import logging
import os
from pathlib import Path

from aind_data_schema.components import subjects
from aind_data_schema.core import subject

from ._instrument import get_photo_ionization_detector, read_rig_model
from ._utils import CALIBRATION_SUBJECT_ID, TrackedDevices, olfactometer_extension_name

logger = logging.getLogger(__name__)


class AindSubjectDataMapper:
    """Maps an olfactometer calibration dataset to an aind-data-schema ``Subject``.

    No animal takes part in an olfactometer calibration, so the subject is a
    :class:`~aind_data_schema.components.subjects.CalibrationObject` describing the
    photo-ionization detector that stands in for the animal's nose.

    See https://docs.allenneuraldynamics.org/en/latest/acquire_upload/calibration.html
    """

    def __init__(self, data_path: os.PathLike):
        self._data_path = Path(data_path)
        self._mapped: subject.Subject | None = None

    @property
    def mapped(self) -> subject.Subject:
        if self._mapped is None:
            raise ValueError("Data has not been mapped yet.")
        return self._mapped

    def is_mapped(self) -> bool:
        return self._mapped is not None

    def map(self) -> subject.Subject:
        logger.info("Mapping aind-data-schema Subject.")
        self._mapped = self._map(self._data_path)
        return self.mapped

    @classmethod
    def _map(cls, root_path: os.PathLike) -> subject.Subject:
        rig = read_rig_model(root_path)

        calibrated_devices = [str(TrackedDevices.OLFACTOMETER)] + [
            olfactometer_extension_name(index) for index, _ in enumerate(rig.harp_olfactometer_extension, start=1)
        ]

        return subject.Subject(
            subject_id=CALIBRATION_SUBJECT_ID,
            subject_details=subjects.CalibrationObject(
                empty=False,
                description=(
                    "Photo-ionization detector placed at the odor port in lieu of an animal, used to "
                    f"measure the odor delivered by {', '.join(calibrated_devices)}."
                ),
                objects=[get_photo_ionization_detector()],
            ),
        )

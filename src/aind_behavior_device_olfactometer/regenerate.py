from pathlib import Path
from typing import Union

import pydantic
from aind_behavior_services.schema import BonsaiSgenSerializers, convert_pydantic_to_bonsai
from aind_behavior_services.session import Session

from . import rig, task_logic

SCHEMA_ROOT = Path("./schema/")
EXTENSIONS_ROOT = Path("./src/Extensions/")
NAMESPACE_PREFIX = "AindBehaviorTelekinesisDataSchema"


def main():
    models = [
        task_logic.OlfactometerCalibrationLogic,
        rig.OlfactometerCalibrationRig,
        Session,
    ]
    model = pydantic.RootModel[Union[tuple(models)]]

    convert_pydantic_to_bonsai(
        model,
        model_name="aind_behavior_telekinesis",
        root_element="Root",
        cs_namespace=NAMESPACE_PREFIX,
        json_schema_output_dir=SCHEMA_ROOT,
        cs_output_dir=EXTENSIONS_ROOT,
        cs_serializer=[BonsaiSgenSerializers.JSON],
    )


if __name__ == "__main__":
    main()

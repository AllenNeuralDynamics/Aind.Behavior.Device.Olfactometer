import os
import unittest
from pathlib import Path
from typing import Dict

from aind_behavior_services.utils import run_bonsai_process

from . import build_examples


class BonsaiTests(unittest.TestCase):
    def test_deserialization(self):
        build_examples()
        JSON_ROOT = Path("./local").resolve()
        MODULE_NAME = "olfactometer"
        workflow_props: Dict[str, str] = {}

        workflow_props["RigPath"] = JSON_ROOT / f"{MODULE_NAME}_rig.json"
        workflow_props["TaskLogicPath"] = JSON_ROOT / f"{MODULE_NAME}_calibration_logic.json"
        workflow_props["SessionPath"] = JSON_ROOT / f"{MODULE_NAME}_session.json"

        for _, file in workflow_props.items():
            if not os.path.exists(file):
                raise FileNotFoundError(f"File {file} does not exist")

        completed_proc = run_bonsai_process(
            workflow_file=Path("./src/unit_tests.bonsai").resolve(),
            is_editor_mode=False,
            layout=None,
            additional_properties=workflow_props,
        )

        self.assertEqual(completed_proc.stderr.decode(), "", f"error:\n {completed_proc.stderr.decode()}")
        self.assertEqual(completed_proc.returncode, 0)


if __name__ == "__main__":
    unittest.main()

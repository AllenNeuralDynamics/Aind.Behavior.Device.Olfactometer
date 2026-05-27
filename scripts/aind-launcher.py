import logging
from pathlib import Path

import clabe.resource_monitor
from aind_behavior_services.session import Session
from clabe.apps import (
    AindBehaviorServicesBonsaiApp,
)
from clabe.data_transfer.robocopy import RobocopyService, RobocopySettings
from clabe.launcher import Launcher, LauncherCliArgs, experiment
from clabe.pickers import DefaultBehaviorPicker, DefaultBehaviorPickerSettings
from clabe.utils import utcnow
from pydantic_settings import CliApp

from aind_behavior_device_olfactometer.rig import OlfactometerCalibrationRig
from aind_behavior_device_olfactometer.task_logic import OlfactometerCalibrationLogic, OlfactometerCalibrationParameters

logger = logging.getLogger(__name__)


@experiment()
async def calibration_experiment(launcher: Launcher) -> None:
    # Start experiment setup
    picker = DefaultBehaviorPicker(
        launcher=launcher,
        settings=DefaultBehaviorPickerSettings(
            config_library_dir=r"\\allen\aind\scratch\AindBehavior.db\AindBehaviorDeviceOlfactometer",
        ),
    )
    experimenter = picker.prompt_experimenter()
    assert experimenter is not None and len(experimenter) > 0, (
        "Experimenter selection is required to proceed with the experiment setup."
    )
    # Pick and register session
    session = Session(
        subject="CALIBRATION",
        experiment="CALIBRATION",
        date=utcnow(),
        allow_dirty_repo=False,
        experimenter=experimenter,
        notes="Session for rig calibration. No actual experiment data will be recorded.",
    )

    task_logic = OlfactometerCalibrationLogic(task_parameters=OlfactometerCalibrationParameters())
    launcher.ui_helper.print(f"Loading task logic with default parameters: {task_logic.task_parameters}")
    skip_manual_task = launcher.ui_helper.prompt_yes_no_question(
        "Skip manual task parameter configuration and use defaults?"
    )
    if not skip_manual_task:
        task_logic = picker.pick_task(OlfactometerCalibrationLogic)

    rig = picker.pick_rig(OlfactometerCalibrationRig)

    launcher.register_session(session, rig.data_directory)

    clabe.resource_monitor.ResourceMonitor(
        constrains=[
            clabe.resource_monitor.available_storage_constraint_factory(rig.data_directory, 2e10),
        ]
    ).run()

    bonsai_app = AindBehaviorServicesBonsaiApp(
        workflow=Path(r"./src/main.bonsai"),
        temp_directory=launcher.temp_dir,
        rig=rig,
        session=session,
        task=task_logic,
    )
    await bonsai_app.run_async()

    # Run data qc
    if picker.ui_helper.prompt_yes_no_question("Would you like to generate a qc report?"):
        try:
            import webbrowser

            from contraqctor.qc.reporters import HtmlReporter

            from aind_behavior_device_olfactometer import data_contract
            from aind_behavior_device_olfactometer.data_qc.data_qc import make_qc_runner

            vr_dataset = data_contract.dataset(launcher.session_directory)
            runner = make_qc_runner(vr_dataset)
            qc_path = launcher.session_directory / "Behavior" / "Logs" / "qc_report.html"
            reporter = HtmlReporter(output_path=qc_path)
            runner.run_all_with_progress(reporter=reporter)
            webbrowser.open(qc_path.as_uri(), new=2)
        except Exception as e:
            logger.error("Failed to run data QC: %s", e)

    # Transfer data
    is_transfer = picker.ui_helper.prompt_yes_no_question("Would you like to transfer data?")
    if not is_transfer:
        logger.info("Data transfer skipped by user.")
        return

    launcher.copy_logs()
    RobocopyService(source=launcher.session_directory, settings=RobocopySettings()).transfer()
    return


class ClabeCli(LauncherCliArgs):
    def cli_cmd(self):
        launcher = Launcher(settings=self)
        launcher.run_experiment(calibration_experiment)
        return None


def main() -> None:
    CliApp().run(ClabeCli)


if __name__ == "__main__":
    main()

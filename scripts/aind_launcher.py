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
from pydantic_settings import CliApp

from aind_behavior_device_olfactometer.rig import OlfactometerCalibrationRig
from aind_behavior_device_olfactometer.task_logic import OlfactometerCalibrationLogic

logger = logging.getLogger(__name__)


@experiment()
async def calibration_experiment(launcher: Launcher) -> None:
    # Start experiment setup
    picker = DefaultBehaviorPicker(
        launcher=launcher,
        settings=DefaultBehaviorPickerSettings(
            config_library_dir=r"\\allen\aind\scratch\AindBehavior.db\AindBehaviorDeviceOlfactometer",
        ),
        experimenter_validator=None,
    )

    session = picker.pick_session(Session)
    task_logic = picker.pick_task(OlfactometerCalibrationLogic)
    rig = picker.pick_rig(OlfactometerCalibrationRig)
    ensure_rig_and_computer_name(rig)

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
            logger.error(f"Failed to run data QC: {e}")

    # Transfer data
    is_transfer = picker.ui_helper.prompt_yes_no_question("Would you like to transfer data?")
    if not is_transfer:
        logger.info("Data transfer skipped by user.")
        return

    launcher.copy_logs()
    RobocopyService(source=launcher.session_directory, settings=RobocopySettings()).transfer()
    return


def ensure_rig_and_computer_name(rig: OlfactometerCalibrationRig) -> None:
    """Ensures rig and computer name are set from environment variables if available, otherwise defaults to rig configuration values."""

    import os

    rig_name = os.environ.get("aibs_comp_id", None)
    computer_name = os.environ.get("hostname", None)

    if rig_name is None:
        logger.warning(
            "'aibs_comp_id' environment variable not set. Defaulting to rig name from configuration. %s", rig.rig_name
        )
        rig_name = rig.rig_name
    if computer_name is None:
        computer_name = rig.computer_name
        logger.warning(
            "'hostname' environment variable not set. Defaulting to computer name from configuration. %s",
            rig.computer_name,
        )

    if rig_name != rig.rig_name or computer_name != rig.computer_name:
        logger.warning(
            "Rig name or computer name from environment variables do not match the rig configuration. "
            "Forcing rig name: %s and computer name: %s from environment variables.",
            rig_name,
            computer_name,
        )
        rig.rig_name = rig_name
        rig.computer_name = computer_name


class ClabeCli(LauncherCliArgs):
    def cli_cmd(self):
        launcher = Launcher(settings=self)
        launcher.run_experiment(calibration_experiment)
        return None


def main() -> None:
    CliApp().run(ClabeCli)


if __name__ == "__main__":
    main()

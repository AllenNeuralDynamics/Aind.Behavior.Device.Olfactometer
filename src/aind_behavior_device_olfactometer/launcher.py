from pathlib import Path

from aind_behavior_services.session import AindBehaviorSessionModel
from clabe import resource_monitor
from clabe.apps import AindBehaviorServicesBonsaiApp, BonsaiAppSettings
from clabe.launcher import DefaultBehaviorPicker, DefaultBehaviorPickerSettings, Launcher, LauncherCliArgs
from pydantic_settings import CliApp

from .rig import OlfactometerCalibrationRig
from .task_logic import OlfactometerCalibrationLogic


def make_launcher(settings: LauncherCliArgs) -> Launcher:
    monitor = resource_monitor.ResourceMonitor(
        constrains=[
            resource_monitor.available_storage_constraint_factory(settings.data_dir, 2e11),
        ]
    )
    app = AindBehaviorServicesBonsaiApp(settings=BonsaiAppSettings(workflow=Path(r"./src/main.bonsai")))
    picker = DefaultBehaviorPicker[OlfactometerCalibrationRig, AindBehaviorSessionModel, OlfactometerCalibrationLogic](
        settings=DefaultBehaviorPickerSettings()  # type: ignore[call-arg]
    )
    launcher = Launcher(
        rig=OlfactometerCalibrationRig,
        session=AindBehaviorSessionModel,
        task_logic=OlfactometerCalibrationLogic,
        settings=settings,
    )

    launcher.register_callable(
        [
            picker.initialize,
            picker.pick_session,
            picker.pick_task_logic,
            picker.pick_rig,
        ]
    )
    launcher.register_callable(monitor.build_runner())
    launcher.register_callable(app.build_runner(allow_std_error=True))
    return launcher


def main():
    args = CliApp().run(LauncherCliArgs)
    launcher = make_launcher(args)
    launcher.main()
    return None


if __name__ == "__main__":
    main()

import typing as t

from pydantic import Field, RootModel
from pydantic_settings import BaseSettings, CliApp, CliSubCommand

from aind_behavior_device_olfactometer import __semver__, regenerate
from aind_behavior_device_olfactometer.data_qc import DataQcCli


class VersionCli(RootModel):
    root: t.Any

    def cli_cmd(self) -> None:
        print(__semver__)


class DslRegenerateCli(RootModel):
    root: t.Any

    def cli_cmd(self) -> None:
        regenerate.main()


class DeviceOlfactometer(BaseSettings, cli_prog_name="telekinesis", cli_kebab_case=True):
    data_qc: CliSubCommand[DataQcCli] = Field(description="Run data quality checks.")
    version: CliSubCommand[VersionCli] = Field(
        description="Print the version of the telekinesis package.",
    )
    regenerate: CliSubCommand[DslRegenerateCli] = Field(
        description="Regenerate the telekinesis dsl dependencies.",
    )

    def cli_cmd(self):
        return CliApp().run_subcommand(self)


def main():
    CliApp().run(DeviceOlfactometer)


if __name__ == "__main__":
    main()

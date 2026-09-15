import os
import typing as t
from functools import partial
from pathlib import Path

import contraqctor
import semver

from .. import __semver__

# Oldest package version whose data layout is described by a contract in this package. Contract
# modules are named after the package version that introduced them, so a new module is only
# needed when the layout on disk changes, and this bound moves with it.
_MIN_SUPPORTED_VERSION = semver.Version.parse("0.2.0-rc0")


def _dataset_lookup_helper(version: str) -> t.Callable[[Path], contraqctor.contract.Dataset]:
    parsed_version = semver.Version.parse(version)
    if parsed_version >= _MIN_SUPPORTED_VERSION:
        from .v0_2_0 import dataset as _dataset
    else:
        raise ValueError(f"Unsupported version: {version}")
    return partial(_dataset, version=version)


def dataset(path: os.PathLike, version: str = __semver__) -> contraqctor.contract.Dataset:
    """
    Loads the dataset for the Olfactometer calibration procedure from a specified version.

    Args:
        path (os.PathLike): The path to the dataset root directory.
        version (str): The version of the dataset to load. By default, it uses the package version.

    Returns:
        contraqctor.contract.Dataset: The loaded dataset.
    """
    dataset_constructor = _dataset_lookup_helper(version)
    return dataset_constructor(Path(path))


def render_dataset(version: str = __semver__) -> str:
    """Renders the dataset as a tree-like structure for visualization."""
    from contraqctor.contract.utils import print_data_stream_tree_html

    dataset_constructor = _dataset_lookup_helper(version)
    return print_data_stream_tree_html(
        dataset_constructor(Path("<RootPath>")), show_missing_indicator=False, show_type=True
    )

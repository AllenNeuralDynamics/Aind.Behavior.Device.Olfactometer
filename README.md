# aind-behavior-device-olfactometer

![CI](https://github.com/AllenNeuralDynamics/Aind.Behavior.Device.Olfactometer/actions/workflows/aind-behavior-device-olfactometer-cicd.yml/badge.svg)
[![License](https://img.shields.io/badge/license-MIT-brightgreen)](LICENSE)
[![ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

A library with a SDK for the Olfactometer behavior task

---

## 📋 General instructions

This repository follows the project structure laid out in the [Aind.Behavior.Services repository](https://github.com/AllenNeuralDynamics/Aind.Behavior.Services).

---

## 🔧 Prerequisites

[Pre-requisites for running the project can be found here](https://allenneuraldynamics.github.io/Aind.Behavior.Services/articles/requirements.html).

---

## 🚀 Deployment

For convenience, once third-party dependencies are installed, `Bonsai` and `python` virtual environments can be bootstrapped by running:

```powershell
./scripts/deploy.ps1
```

from the root of the repository.

## ⚙️ Generating settings files

The task is instantiated by a set of three settings files that strictly follow a DSL schema. These files are:

- `task_logic.json`
- `rig.json`
- `session.json`

Examples on how to generate these files can be found in the `./examples` directory of the repository. Once generated, these are the only required inputs to run the Bonsai workflow in `./src/main.bonsai`.

The workflow can thus be executed using the [Bonsai CLI](https://bonsai-rx.org/docs/articles/cli.html):

```powershell
"./bonsai/bonsai.exe" "./src/main.bonsai" -p SessionPath=<path-to-session.json> -p RigPath=<path-to-rig.json> -p TaskLogicPath=<path-to-task_logic.json>
```

However, for a better experiment management user experience, it is recommended to use the provided experiment launcher below.

## [> ] CLI tools

### Task CLI

The platform exposes a few CLI tools to facilitate various tasks. Tools are available via:

```powershell
uv run device-olfactometer <subcommand>
```

for a list of all sub commands available:

```powershell
uv run device-olfactometer -h
```

You may need to install optional dependencies depending on the sub-commands you run.



## 🎮 Experiment launcher (CLABE)

To manage experiments and input files, this repository contains a launcher script that can be used to run the Olfactometer task. A default script is located at `./scripts/aind-launcher.py`. It can be run from the command line as follows:

```powershell
uv run clabe run ./scripts/aind-launcher.py
# or uv run ./scripts/aind-launcher.py.py
```

Additional arguments can be passed to the script as needed. For instance to allow the script to run with uncommitted changes in the repository, the `--allow-dirty` flag can be used:

```powershell
uv run clabe run ./scripts/aind-launcher.py --allow-dirty
```

or via a `./local/clabe.yml` file. Additional custom launcher scripts can be created and used as needed. See documentation in the [`clabe` repository](https://allenneuraldynamics.github.io/clabe/) for more details.


## 🔍 Primary data quality-control

Once an experiment is collected, the primary data quality-control script can be run to check the data for issues. This script can be launcher using:

```powershell
uv run device-olfactometer data-qc <path-to-data-dir>
```

## 🔄 Regenerating schemas

DSL schemas can be modified in `./src/aind_behavior_device_olfactometer/rig.py` (or `(...)/task_logic.py`).

Once modified, changes to the DSL must be propagated to `json-schema` and `csharp` API. This can be done by running:

```powershell
uv run device-olfactometer regenerate
```
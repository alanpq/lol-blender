# lol-blender
Blender plugin for League of Legends asset import/export, using [league-toolkit](https://github.com/LeagueToolkit/league-toolkit/).
> **NOTE:** This plugin is *extremely* early in development, see [io_scene_lol](https://github.com/Daniil-SV/io_scene_lol) for a more developed importer/exporter.

# Features
|     ✅     |        ⚠️        |    🛠️    |
| :-------: | :-------------: | :-----: |
| Supported | Partial support | Planned |

## Scene I/O
|                             | Import | Export |
| :-------------------------: | :----: | :----: |
|   **Skinned Mesh** (.skn)   |   ⚠️    |   🛠️    |
|     **Skeleton** (.skl)     |   ⚠️    |   🛠️    |
|    **Animation** (.anm)     |   🛠️    |   🛠️    |
| **Static mesh** (.sco/.scb) |   🛠️    |   🛠️    |
| **Map geometry** (.mapgeo)  |   🛠️    |   🛠️    |


# Contributing
## Prerequisites
- Python 3
- Rust
  - Maturin (see their install guide [here](https://github.com/PyO3/maturin?tab=readme-ov-file#usage))

Clone the project with `--recurse-submodules` or sync the [league-toolkit](https://github.com/LeagueToolkit/league-toolkit/) submodule manually:
```bash
git submodule init # initialize your local configuration file
git submodule update # fetch submodules
```

Create and source a python virtual env:
```bash
python -m venv venv
source venv/bin/activate
```

# Development

Build the league-toolkit bindings:
```bash
cd bindings
maturin develop
```

Run Blender with addon live updating:
```bash
# Path to your blender executable file.
export BLENDER_PATH="/path/to/your/blender/executable"
# Optional, needed if the version can't be detected from BLENDER_PATH
export BLENDER_VERSION="4.1"

# Where to put (dev) addon builds 
# Optional, useful for funky setups (e.g. nix)
export __BLENDER_ADDON_PATH="/path/to/blender/addons"

# Path to the wheel for the league-toolkit bindings
# `maturin develop` puts the wheel in target/wheels/*.whl
export __LOL_WHEEL_PATH="/path/to/project/bindings/target/wheels/league_toolkit-x.x.x-etc-etc.whl"
python test.py
```

# Build Release 
After completing the [prerequisites](#prerequisites), you can build a release .zip of the addon with:
```bash
python release.py
```

Build the league-toolkit bindings, to be distributed separately (for now):
```bash
cd bindings
maturin develop
```
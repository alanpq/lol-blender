# lol-blender
Blender plugin for League of Legends asset import/export, using [league-toolkit](https://github.com/LeagueToolkit/league-toolkit/).
> **NOTE:** This plugin is *extremely* early in development, see [io_scene_lol](https://github.com/Daniil-SV/io_scene_lol) for a more developed importer/exporter.

# Features
|     ✅     |        ⚠️        |   🚨   |    🛠️    |
| :-------: | :-------------: | :----: | :-----: |
| Supported | Partial support | Broken | Planned |

## Scene I/O
|                             | Import | Export |
| :-------------------------: | :----: | :----: |
|   **Skinned Mesh** (.skn)   |   ✅[^1]  |   ⚠️    |
|     **Skeleton** (.skl)     |   ✅   |   🚨   |
|    **Animation** (.anm)     |   🛠️    |   🛠️    |
| **Static mesh** (.sco/.scb) |   🛠️    |   🛠️    |
| **Map geometry** (.mapgeo)  |   🛠️    |   🛠️    |

[^1]: Automatic texture import not yet implemented. (Materials/UV's are imported though, so textures can be manually hooked up)

# How to Install
1. Download the [latest .zip file](https://github.com/alanpq/lol-blender/releases/latest) of the addon (`addon-lol-blender-vX.Y.Z.zip`)
    - There is no need to download any of the `.whl` files (unless you are doing manual setup in step 5).
2. Open Blender and go to `Edit > Preferences > Add-ons`
3. Click the `Install` button in the top right, next to refresh.
4. Select the zip file you downloaded and click install.
5. In the preferences for the addon, click `Automatically download & install dependencies`.
    - This will fetch the correct `.whl` file for your system and install it.
    - If you want to do this manually - or the automatic download isn't working,
      download the correct `.whl` from the releases page, set the `Wheel Path` in your addon preferences, and click `Manually install dependencies`.

# Development
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

## Building/Running

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

## Building for Release
After completing the [prerequisites](#prerequisites), you can build a release .zip of the addon with:
```bash
python release.py
```

Build the league-toolkit bindings, to be distributed separately (for now):
```bash
cd bindings
maturin develop
```

# lol-blender
> **NOTE:** This plugin is *extremely* early in development, see [io_scene_lol](https://github.com/Daniil-SV/io_scene_lol) for a more developed importer/exporter.

# Features
lol-blender is currently too early in development for a feature list to be useful.

# Roadmap
- Skinned mesh (.skn) import/export
  - w/ material/textures
- Skeleton (.skl) import/export
- Animation (.anm) import/export
- Static mesh (.sco/.scb) import/export
- Map geometry (.mapgeo) import/export
  - w/ material/textures



# Development
## Prerequisites
Create and source a python virtual env:
```bash
python -m venv venv
source venv/bin/activate
```

You can then run Blender with addon live updating:
```bash
export BLENDER_PATH="/path/to/your/blender/executable"
python test.py
```

# Building
Assuming you have all [prerequisites](#prerequisites), you can build a release .zip of the addon with:
```bash
python release.py
```

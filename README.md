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
|     **Skeleton** (.skl)     |   ✅   |   ⚠️   |
|    **Animation** (.anm)     |   🛠️    |   🛠️    |
| **Static mesh** (.sco/.scb) |   🛠️    |   🛠️    |
| **Map geometry** (.mapgeo)  |   🛠️    |   🛠️    |

[^1]: Automatic texture import not yet implemented. (Materials/UV's are imported though, so textures can be manually hooked up)

# Development

## Requirements

- [Git](https://git-scm.com/downloads)
- Python
- [Rust](https://www.rust-lang.org/learn/get-started)
  - Maturin (see their install guide [here](https://github.com/PyO3/maturin?tab=readme-ov-file#usage))
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- [VSCode](https://code.visualstudio.com/) with the [Blender Development Addon](https://marketplace.visualstudio.com/items?itemName=JacquesLucke.blender-development)
- [Blender](https://www.blender.org/)

## Setup

- Clone the repository:
  ```bash
  git clone git@github.com:alanpq/lol-blender.git
  cd lol-blender
  ```

- Compile the `rust_wrap` crate:
  ```bash
  cd crates/rust_wrap
  maturin build --release --out ../../addon/wheels/
  ```

- Take note of the output from your `maturin` command (it might differ in your case!):
  ```
  <...>
  📦 Built wheel for CPython 3.11 to ../../addon/wheels/rust_wrap-0.1.0-cp311-cp311-manylinux_2_34_x86_64.whl
  ```

  Make sure it's listed in the `blender_manifest.toml`:
  ```toml
  wheels = [
      "./wheels/rust_wrap-0.1.0-cp311-cp311-manylinux_2_34_x86_64.whl",
      "<...>",
      "<...>",
  ]
  ```

- Compile the `rust_hot` crate (this is the step you'll typically repeat later):
  ```bash
  cd crates/rust_hot
  cargo build --release
  ```

- Open the repository in VSCode, open the Command Palette (`Ctrl+Shift+P`), search for **"Blender: Start"**, and select your Blender executable (mean the one you've installed prior).

> [!IMPORTANT]
> Verify that the VSCode terminal shows: `creating new rust context`

## Hot Reloading

### Python

For the Python parts of the extension (UI and such), use the VSCode addon:
**"Blender: Reload Addons"** in the Command Palette.

### Rust (Core)

Recompile the `rust_hot` crate for changes in the `rust_core` crate:
```bash
cd crates/rust_hot/
cargo build --release
```

> [!NOTE]
> We're editing `rust_core` but recompiling `rust_hot`.

### Rust (API)

For changes in the `rust_api` or `rust_hot` crates themselves, hot reloading isn’t possible with this approach.

You'll need to:
1. Rebuild `rust_wrap` with `maturin` as before.
2. Recompile `rust_hot`.
3. Unload the extension and restart Blender.

## Building Without Hot Reloading

When preparing for distribution, **do not use hot reloading**.

- Compile the `rust_wrap` crate without default features:
  ```bash
  cd crates/rust_wrap/
  maturin build --release --no-default-features --out ../../addon/wheels/
  ```

- No additional Rust steps apply in this case.

- Build the extension via Blender directly:
  ```bash
  cd addon/
  blender --command extension build
  ```

## Troubleshooting

### Missing Wheel
```
RuntimeError: Error: No module named 'rust_wrap'
```
Indicates a missing or incorrect path to the wheel.

---

### Missing Dynamic Library
```
pyo3_runtime.PanicException: failed to create hot reload loader: LibraryLoadError(DlOpen { desc: "<...> (no such file)" })
```
or
```
pyo3_runtime.PanicException: failed to create hot reload loader: LibraryCopyError(Custom { kind: NotFound, error: "file <...>" does not exist" })
```
Indicates the dynamic library for hot reloading is missing.

Make sure `rust_hot` is built with:
```bash
cargo build [--release]
```
(Release/debug builds of the wrap and core crates must match.)

---

### Poisoned
```
pyo3_runtime.PanicException: Once instance has previously been poisoned
```
Means the reloader thread has failed.

Disable the extension and restart Blender.

# Credits
Thanks to Algebraic UG for their [work on Blender extensions with hot reloadable Rust parts](https://github.com/Algebraic-UG/blend_rust), from which this project heavily takes from.
![Featured Image](assets/featured.svg)

# Blend Rust

This is an example Blender extension demonstrating how to build a Blender extension with reloadable Rust parts.
The example is meant to be extensible. Tested on Ubuntu 24.04, Windows 11, and macOS 14.7.3.

For more information about this project, read the [blog entry](https://algebraic.games/blog/rust_extension_api/).

> [!WARNING]
> This is not mature in any sense, and there are several subtle ways to mess up.

## Requirements

- [Git](https://git-scm.com/downloads)
- [Rust](https://www.rust-lang.org/learn/get-started)
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- [VSCode](https://code.visualstudio.com/) with the [Blender Development Addon](https://marketplace.visualstudio.com/items?itemName=JacquesLucke.blender-development)
- [Blender](https://www.blender.org/)

## Setup

- Clone the repository:
  ```bash
  git clone git@github.com:Vollkornaffe/blend_rust.git
  ```

- Compile the `rust_wrap` crate:
  ```bash
  cd blend_rust/rust_wrap/
  uvx --python 3.11 maturin build --release --out ../python/wheels/
  ```

- Take note of the output from your `uvx` command (it might differ in your case!):
  ```
  <...>
  📦 Built wheel for CPython 3.11 to ../python/wheels/rust_wrap-0.1.0-cp311-cp311-manylinux_2_34_x86_64.whl
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
  cd blend_rust/rust_hot/
  cargo build --release
  ```

- Open the `blend_rust/python` folder in VSCode, open the Command Palette (`Ctrl+Shift+P`), search for **"Blender: Build and Start"**, and select your Blender executable (mean the one you've installed prior).

> [!IMPORTANT]
> Verify that the VSCode terminal shows: `creating new rust context`

## Usage

Select any mesh object in the scene and find **"Sample Object's Inside"** via `F3`.
Alternatively, you’ll find it in the **Object** menu.

You should see a new object consisting only of points that are inside the selected mesh!

## Hot Reloading

### Python

For the Python parts of the extension (UI and such), use the VSCode addon:
**"Blender: Reload Addons"** in the Command Palette.

### Rust (Core)

Recompile the `rust_hot` crate for changes in the `rust_core` crate:
```bash
cd blend_rust/rust_hot/
cargo build --release
```

> [!NOTE]
> We're editing `rust_core` but recompiling `rust_hot`.

This is ideal when your interface rarely changes while working on core functionality — which is pretty much the entire point of this repo.

### Rust (API)

For changes in the `rust_api` or `rust_hot` crates themselves, hot reloading isn’t possible with this approach.

You'll need to:
1. Rebuild `rust_wrap` with `uvx` as before.
2. Recompile `rust_hot`.
3. Unload the extension and restart Blender.

## (More) Restrictions for Hot Reloading Rust

Replacing parts of the implementation at runtime isn’t something the Rust compiler can make completely safe.

As mentioned earlier:
- Only the `rust_core` crate can be hot reloaded.
- You must ensure that any threads and resources are cleanly joined and dropped when loading a new version. (In this simple example, neither applies.)

You can achieve this by implementing `Drop` for the `Impl` of `Context`.

Anything exposed to Python through `rust_wrap` should be defined in `rust_api` or `rust_hot`.
New traits, functions, structs, enums, etc., and changes to them are **not reloadable**.

> [!TIP]
> If parts of your API need to be flexible, consider passing serialized data (e.g., JSON) — or something more sophisticated, like RPC.

## Building Without Hot Reloading

When preparing for distribution, **do not use hot reloading**.

- Compile the `rust_wrap` crate without default features:
  ```bash
  cd blend_rust/rust_wrap/
  uvx --python 3.11 maturin build --release --no-default-features --out ../python/wheels/
  ```

- No additional Rust steps apply in this case.

- Instead of using the VSCode addon, build the extension via Blender directly:
  ```bash
  cd blend_rust/python/
  blender --command extension build
  ```

> [!TIP]
> You’ll probably want to either build wheels for other platforms or comment them out in the `blend_rust/python/blender_manifest.toml`.

## Troubleshooting

A few pitfalls I’ve encountered myself:

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
use std::{collections::HashMap, path::PathBuf};

use anyhow::Result;
use numpy::{PyArray1, PyReadonlyArray1, PyReadonlyArray3, PyReadonlyArray4, PyReadonlyArray5};
use pyo3::prelude::*;

mod hot_reloadable;

use hot_reloadable::{initialize, with_context};

#[cfg(feature = "hot_reload")]
use hot_reloadable::handle_reload;

use rust_hot::rust_api::{Bone, Skl, Skn};

#[pyfunction]
fn version() -> PyResult<&'static str> {
    Ok(std::env!("CARGO_PKG_VERSION"))
}

pub type Vec3 = [f32; 3];
pub type Vec4 = [f32; 4];
pub type Mat4 = [[f32; 4]; 4];

#[pyfunction]
fn import_skn<'py>(py: Python<'py>, path: PathBuf) -> Result<Skn> {
    println!("importing skn: {path:?}");
    with_context(|context| context.import_skn(path))?
}

#[pyfunction]
fn import_skl<'py>(py: Python<'py>, path: PathBuf) -> Result<Skl> {
    println!("importing skl: {path:?}");
    with_context(|context| context.import_skl(py, path))?
}

#[pyfunction]
fn export_skn<'py>(
    path: PathBuf,
    vertex_positions: PyReadonlyArray1<'py, f32>,
    vertex_normals: PyReadonlyArray1<'py, f32>,
    vertex_blend_indices: PyReadonlyArray1<'py, u8>,
    vertex_blend_weights: PyReadonlyArray1<'py, f32>,
    vertex_uvs: PyReadonlyArray1<'py, u8>,
    triangles: PyReadonlyArray1<'py, i64>,
) -> Result<()> {
    println!("exporting skn: {path:?}");

    with_context(|context| {
        context.export_skn(
            path,
            vertex_positions.as_slice()?,
            vertex_normals.as_slice()?,
            vertex_blend_indices.as_slice()?,
            vertex_blend_weights.as_slice()?,
            vertex_uvs.as_slice()?,
            triangles.as_slice()?,
        )
    })?
}

#[pyfunction]
fn export_skl<'py>(
    bones: HashMap<String, PyRef<'_, Bone>>,
    path: Option<PathBuf>,
) -> Result<HashMap<String, u8>> {
    println!("exporting skl: {path:?} ");
    with_context(|context| context.export_skl(path, bones))?
}

/// A Python module implemented in Rust. The name of this function must match
/// the `lib.name` setting in the `Cargo.toml`, else Python will not be able to
/// import the module.
#[pymodule]
fn rust_wrap(m: &Bound<'_, PyModule>) -> PyResult<()> {
    initialize();

    #[cfg(feature = "hot_reload")]
    handle_reload();

    m.add_class::<Bone>()?;

    m.add_function(wrap_pyfunction!(version, m)?)?;

    m.add_function(wrap_pyfunction!(import_skn, m)?)?;
    m.add_function(wrap_pyfunction!(import_skl, m)?)?;

    m.add_function(wrap_pyfunction!(export_skn, m)?)?;
    m.add_function(wrap_pyfunction!(export_skl, m)?)?;
    Ok(())
}

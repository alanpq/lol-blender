use std::{collections::HashMap, path::PathBuf};

use anyhow::Result;
use numpy::{PyArray1, PyReadonlyArray1};
use pyo3::prelude::*;

mod hot_reloadable;
use hot_reloadable::{handle_reload, initialize, with_context};

#[pyfunction]
fn version() -> PyResult<&'static str> {
    Ok(std::env!("CARGO_PKG_VERSION"))
}

#[pyfunction]
fn sample_inside<'py>(
    py: Python<'py>,
    flat_vertices: PyReadonlyArray1<'py, f32>,
    flat_triangles: PyReadonlyArray1<'py, i32>,
) -> Result<Bound<'py, PyArray1<f32>>> {
    let flat_vertices = flat_vertices.as_slice()?;
    let flat_triangles = flat_triangles.as_slice()?;

    let flat_samples =
        with_context(|context| context.sample_inside(flat_vertices, flat_triangles))?;

    Ok(PyArray1::from_vec(py, flat_samples))
}


pub type Vec3 = [f32; 3];
pub type Vec4 = [f32; 4];
pub type Mat4 = [[f32; 4]; 4];

#[derive(Debug)]
#[pyclass]
pub struct Skn {
    #[pyo3(get)]
    pub vertex_positions: Vec<Vec3>,
    #[pyo3(get)]
    pub vertex_normals: Vec<u32>,

    #[pyo3(get)]
    pub vertex_blend_indices: Vec<[u8; 4]>,
    #[pyo3(get)]
    pub vertex_blend_weights: Vec<[f32; 4]>,
    #[pyo3(get)]
    pub vertex_uvs: Vec<[u8; 2]>,

    #[pyo3(get)]
    pub triangles: Vec<[u32; 3]>,

    #[pyo3(get)]
    pub material_ranges: Vec<MaterialRange>,
}

#[derive(Debug, Clone)]
#[pyclass]
pub struct MaterialRange {
    #[pyo3(get)]
    pub material: String,
    #[pyo3(get)]
    pub start_vertex: i32,
    #[pyo3(get)]
    pub vertex_count: i32,
    #[pyo3(get)]
    pub start_index: i32,
    #[pyo3(get)]
    pub index_count: i32,
}


#[derive(Debug)]
#[pyclass]
pub struct Skl {
    #[pyo3(get)]
    pub parents: Vec<Option<String>>,
    #[pyo3(get)]
    pub names: Vec<String>,
    #[pyo3(get)]
    pub ibms: Vec<Mat4>,
    #[pyo3(get)]
    pub locals: Vec<Mat4>,
    #[pyo3(get)]
    pub is_influences: Vec<bool>,

    #[pyo3(get)]
    pub influence_lookup: HashMap<i16, String>,
}



#[pyfunction]
fn import_skn<'py>(
    py: Python<'py>,
    path: PathBuf,
) -> Result<Skn> {
    println!("importing skn: {path:?}");
    anyhow::bail!("todo")
}

#[pyfunction]
fn import_skl<'py>(
    py: Python<'py>,
    path: PathBuf,
) -> Result<Skl> {
    println!("importing skl: {path:?}");
    anyhow::bail!("todo")
}

/// A Python module implemented in Rust. The name of this function must match
/// the `lib.name` setting in the `Cargo.toml`, else Python will not be able to
/// import the module.
#[pymodule]
fn rust_wrap(m: &Bound<'_, PyModule>) -> PyResult<()> {
    initialize();

    #[cfg(feature = "hot_reload")]
    handle_reload();

    m.add_function(wrap_pyfunction!(sample_inside, m)?)?;
    m.add_function(wrap_pyfunction!(version, m)?)?;
    m.add_function(wrap_pyfunction!(import_skn, m)?)?;
    Ok(())
}

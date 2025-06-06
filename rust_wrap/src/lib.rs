use anyhow::Result;
use numpy::{PyArray1, PyReadonlyArray1};
use pyo3::prelude::*;

mod hot_reloadable;
use hot_reloadable::{handle_reload, initialize, with_context};

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

/// A Python module implemented in Rust. The name of this function must match
/// the `lib.name` setting in the `Cargo.toml`, else Python will not be able to
/// import the module.
#[pymodule]
fn rust_wrap(m: &Bound<'_, PyModule>) -> PyResult<()> {
    initialize();

    #[cfg(feature = "hot_reload")]
    handle_reload();

    m.add_function(wrap_pyfunction!(sample_inside, m)?)?;
    Ok(())
}

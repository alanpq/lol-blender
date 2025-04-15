mod skl;
mod skn;
mod anm;

pub use skl::*;
pub use skn::*;
pub use anm::*;

use pyo3::prelude::*;
pub fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    //m.add_class::<Vertex>()?;
    m.add_function(wrap_pyfunction!(import_skn, m)?)?;

    //m.add_class::<Bone>()?;
    m.add_function(wrap_pyfunction!(import_skl, m)?)?;

    m.add_function(wrap_pyfunction!(import_anm, m)?)?;
    Ok(())
}

pub mod skn;
pub use skn::*;

use pyo3::prelude::*;
pub fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    //m.add_class::<Vertex>()?;
    m.add_function(wrap_pyfunction!(import_skn, m)?)?;

    //m.add_class::<Bone>()?;
    //m.add_function(wrap_pyfunction!(export_skl, m)?)?;
    Ok(())
}

mod bone;
mod skl;
mod skn;
mod vertex;
pub use bone::*;
pub use skl::*;
pub use skn::*;
pub use vertex::*;

use pyo3::prelude::*;
pub fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<Vertex>()?;
    m.add_function(wrap_pyfunction!(export_skn, m)?)?;

    m.add_class::<Bone>()?;
    m.add_function(wrap_pyfunction!(export_skl, m)?)?;
    Ok(())
}

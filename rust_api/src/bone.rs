use crate::Mat4;
use pyo3::prelude::*;

#[derive(Debug)]
#[pyclass]
pub struct Bone {
    #[pyo3(get, set)]
    pub parent: Option<String>,
    pub ibm: Mat4,
    pub local: Mat4,
    pub is_influence: bool,
}

#[pymethods]
impl Bone {
    #[new]
    fn py_new(parent: String, local: Mat4, ibm: Mat4, is_influence: bool) -> Self {
        Self {
            parent: match parent.is_empty() {
                true => None,
                false => Some(parent),
            },
            ibm,
            local,
            is_influence,
        }
    }
}

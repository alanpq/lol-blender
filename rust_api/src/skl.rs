use std::collections::HashMap;

use pyo3::prelude::*;

use crate::Mat4;

#[derive(Debug)]
#[pyclass]
pub struct Skl {
    #[pyo3(get)]
    pub influence_lookup: HashMap<u32, String>,

    #[pyo3(get)]
    pub joints: Vec<Py<Joint>>,
}

#[derive(Debug)]
#[pyclass]
pub struct Joint {
    #[pyo3(get, set)]
    pub parent: Option<String>,
    #[pyo3(get, set)]
    pub name: String,
    #[pyo3(get, set)]
    pub ibm: Mat4,
    #[pyo3(get, set)]
    pub local: Mat4,
    #[pyo3(get, set)]
    pub is_influence: bool,
}

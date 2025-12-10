use std::collections::HashMap;

use pyo3::prelude::*;

use crate::Mat4;

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

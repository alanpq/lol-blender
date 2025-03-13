use lib::core::animation::RigResource;
use pyo3::prelude::*;
use std::{collections::HashMap, fs::File, io::BufReader, path::PathBuf};

use crate::{skinned::export::Bone, Mat4};

#[derive(Debug)]
#[pyclass]
pub struct Skl {
    #[pyo3(get)]
    pub joints: Vec<Py<Joint>>,

    #[pyo3(get)]
    pub influence_lookup: HashMap<i16, String>,
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

#[pyfunction]
pub fn import_skl(py: Python<'_>, path: PathBuf) -> PyResult<Skl> {
    let mut file = File::open(path).map(BufReader::new).unwrap();
    let skl = RigResource::from_reader(&mut file).unwrap();

    skl.joints();
    Ok(Skl {
        joints: skl
            .joints()
            .iter()
            .map(|j| {
                Py::new(
                    py,
                    Joint {
                        parent: match j.parent_id() {
                            -1 => None,
                            id => skl.joints().get(id as usize).map(|j| j.name().into()),
                        },
                        name: j.name().into(),
                        ibm: j.inverse_bind_transform().transpose().to_cols_array_2d(),
                        local: j.local_transform().transpose().to_cols_array_2d(),
                        is_influence: false,
                    },
                )
                .unwrap()
            })
            .collect(),

        influence_lookup: skl
            .influences()
            .iter()
            .enumerate()
            .map(|(influence_idx, bone_idx)| {
                (
                    influence_idx as i16,
                    skl.joints().get(*bone_idx as usize).unwrap().name().into(),
                )
            })
            .collect(),
    })
}

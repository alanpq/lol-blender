use crate::skinned::export::Vertex;
use itertools::{izip, Itertools};
use lib::core::{mem::ElementName, mesh::SkinnedMesh};
use pyo3::prelude::*;
use std::{fs::File, io::BufReader, path::PathBuf};

#[derive(Debug)]
#[pyclass]
pub struct Skn {
    #[pyo3(get, set)]
    pub vertices: Vec<Py<Vertex>>,
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

#[pyfunction]
pub fn import_skn(py: Python<'_>, path: PathBuf) -> PyResult<Skn> {
    let mut file = File::open(path).map(BufReader::new).unwrap();
    let skn = SkinnedMesh::from_reader(&mut file).unwrap();

    let positions = skn
        .vertex_buffer()
        .accessor::<glam::Vec3>(ElementName::Position)
        .unwrap();
    let normals = skn
        .vertex_buffer()
        .accessor::<glam::Vec3>(ElementName::Normal)
        .unwrap();
    let indices = skn
        .vertex_buffer()
        .accessor::<[u8; 4]>(ElementName::BlendIndex)
        .unwrap();
    let weights = skn
        .vertex_buffer()
        .accessor::<glam::Vec4>(ElementName::BlendWeight)
        .unwrap();

    Ok(Skn {
        vertices: izip!(
            positions.iter(),
            normals.iter(),
            indices.iter(),
            weights.iter()
        )
        .map(|(pos, norm, blend_indices, blend_weights)| {
            Py::new(
                py,
                Vertex {
                    pos: pos.into(),
                    normal: norm.into(),
                    blend_indices,
                    blend_weights: blend_weights.into(),
                },
            )
            .unwrap()
        })
        .collect(),
        triangles: skn
            .index_buffer()
            .iter()
            .chunks(3)
            .into_iter()
            .map(|tri| {
                tri.collect_array::<3>()
                    .expect("index buffer to be multiple of 3")
            })
            .collect(),
        material_ranges: skn
            .ranges()
            .iter()
            .map(|r| MaterialRange {
                material: r.material.clone(),
                start_vertex: r.start_vertex,
                vertex_count: r.vertex_count,
                start_index: r.start_index,
                index_count: r.index_count,
            })
            .collect(),
    })
}

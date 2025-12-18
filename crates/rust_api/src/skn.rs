use pyo3::prelude::*;

use crate::Vec3;

#[derive(Debug)]
#[pyclass]
pub struct Skn {
    #[pyo3(get)]
    pub vertex_count: u32,

    #[pyo3(get)]
    pub vertex_positions: Vec<Vec3>,
    #[pyo3(get)]
    pub vertex_normals: Vec<Vec3>,

    #[pyo3(get)]
    pub vertex_blend_indices: Vec<u8>,
    #[pyo3(get)]
    pub vertex_blend_weights: Vec<f32>,
    #[pyo3(get)]
    pub vertex_uvs: Vec<[f32; 2]>,

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

use crate::Vec3;
use pyo3::prelude::*;

#[derive(Debug)]
#[pyclass]
pub struct Vertex {
    #[pyo3(get, set)]
    pub pos: Vec3,
    #[pyo3(get, set)]
    pub normal: Vec3,

    #[pyo3(get, set)]
    pub blend_indices: [u8; 4],
    #[pyo3(get, set)]
    pub blend_weights: [f32; 4],
}

#[pymethods]
impl Vertex {
    #[new]
    pub fn py_new(
        pos: Vec3,
        normal: Vec3,
        blend_indices: Option<[u8; 4]>,
        blend_weights: Option<[f32; 4]>,
    ) -> Self {
        Self {
            pos,
            normal,
            blend_indices: blend_indices.unwrap_or_default(),
            blend_weights: blend_weights.unwrap_or_default(),
        }
    }
}

impl Vertex {
    pub fn push_bytes(&self, v: &mut Vec<u8>) {
        // 52 total
        for i in self.pos {
            // POSITION (12)
            v.extend_from_slice(&i.to_le_bytes())
        }
        v.extend(self.blend_indices); // BLEND_INDEX (4)
        v.extend(self.blend_weights.iter().flat_map(|w| w.to_le_bytes())); // BLEND_WEIGHT (16)

        for i in self.normal {
            // NORMAL (12)
            v.extend_from_slice(&i.to_le_bytes())
        }
        v.extend([0_u8; 8]); // TEXCOORD_0 (8)
    }
}

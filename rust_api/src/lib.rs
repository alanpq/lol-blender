use std::{collections::HashMap, path::PathBuf};

mod bone;
pub use bone::*;

mod skn;
use pyo3::{PyRef, Python};
pub use skn::*;

mod skl;
pub use skl::*;

pub type Vec3 = [f32; 3];
pub type Vec4 = [f32; 4];
pub type Mat4 = [[f32; 4]; 4];

pub trait Context: Send + Sync {
    fn import_skn(&self, path: PathBuf) -> Result<Skn, anyhow::Error>;
    fn import_skl(&self, py: Python<'_>, path: PathBuf) -> Result<Skl, anyhow::Error>;

    #[allow(clippy::too_many_arguments)]
    fn export_skn(
        &self,
        path: PathBuf,
        vertex_positions: &[f32],
        vertex_normals: &[f32],
        vertex_blend_indices: &[u8],
        vertex_blend_weights: &[f32],
        vertex_uvs: &[u8],
        triangles: &[i64],
    ) -> Result<(), anyhow::Error>;

    fn export_skl(
        &self,
        path: Option<PathBuf>,
        bones: HashMap<String, PyRef<'_, Bone>>,
    ) -> Result<HashMap<String, u8>, anyhow::Error>;
}

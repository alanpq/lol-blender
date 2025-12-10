use nalgebra::{Matrix3, Vector3};
use pyo3::PyRef;
use rust_api::{Bone, Context, Skl, Skn};

pub struct Impl;
impl Context for Impl {
    fn import_skl(&self, path: std::path::PathBuf) -> Result<Skl, anyhow::Error> {
        anyhow::bail!("TODO");
    }
    fn import_skn(&self, path: std::path::PathBuf) -> Result<Skn, anyhow::Error> {
        anyhow::bail!("TODO");
    }

    fn export_skl(
        &self,
        path: std::path::PathBuf,
        bones: std::collections::HashMap<String, PyRef<'_, Bone>>,
    ) -> Result<std::collections::HashMap<String, u8>, anyhow::Error> {
        anyhow::bail!("TODO");
    }

    fn export_skn(
        &self,
        path: std::path::PathBuf,
        vertex_positions: &[f32],
        vertex_normals: &[f32],
        vertex_blend_indices: &[u8],
        vertex_blend_weights: &[f32],
        vertex_uvs: &[u8],
        triangles: &[i64],
    ) -> Result<(), anyhow::Error> {
        anyhow::bail!("TODO");
    }
}

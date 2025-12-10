use std::{
    collections::{BTreeMap, HashMap},
    fs::File,
    io::BufReader,
};

use itertools::Itertools;
use league_toolkit::{
    anim::RigResource,
    mesh::{SkinnedMesh, mem::vertex::ElementName},
};
use pyo3::{Py, PyRef, Python};
use rust_api::{Bone, Context, Joint, MaterialRange, Skl, Skn};

pub struct Impl;
impl Context for Impl {
    fn import_skl(&self, py: Python<'_>, path: std::path::PathBuf) -> Result<Skl, anyhow::Error> {
        let mut file = File::open(path).map(BufReader::new).unwrap();
        let skl = RigResource::from_reader(&mut file).unwrap();

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
                        influence_idx as u32,
                        skl.joints().get(*bone_idx as usize).unwrap().name().into(),
                    )
                })
                .collect(),
        })
    }
    fn import_skn(&self, path: std::path::PathBuf) -> Result<Skn, anyhow::Error> {
        let mut file = File::open(path).map(BufReader::new)?;
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
        let uvs = skn
            .vertex_buffer()
            .accessor::<glam::Vec2>(ElementName::Texcoord0)
            .unwrap();

        let vertex_positions = positions.iter().map(|p| p.into()).collect_vec();
        let vertex_blend_indices = indices.iter().flatten().collect_vec();
        let vertex_blend_weights: Vec<f32> = weights.iter().flat_map(|w| w.to_array()).collect();

        Ok(Skn {
            vertex_count: vertex_positions.len() as u32,
            vertex_positions,
            vertex_normals: normals.iter().map(|p| p.into()).collect(),
            vertex_blend_indices,
            vertex_blend_weights,
            vertex_uvs: uvs.iter().map(|p| p.into()).collect(),

            triangles: skn
                .index_buffer()
                .iter()
                .map(|idx| idx.into())
                .chunks(3)
                .into_iter()
                .map(|tri| {
                    tri.collect_array::<3>()
                        .expect("index buffer must be multiple of 3")
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

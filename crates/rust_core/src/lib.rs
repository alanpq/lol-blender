//! Hot reloadable core impl of our extension
//! Only this can be hot reloaded.
//!
//! You must ensure any threads and resources are cleanly joined and dropped when loading a new version
//!   - via `Drop` for our `Context` implementor `Impl`.
//! Anything exposed to Python through `rust_wrap` should be defined in `rust_api` or `rust_hot`.
//! New traits, functions, structs, enums, etc., and changes to them are **not reloadable**.

use std::{
    collections::{BTreeMap, HashMap, VecDeque},
    fs::File,
    io::{BufReader, BufWriter},
};

use itertools::Itertools;
use league_toolkit::{
    anim::{RigResource, joint},
    mesh::{
        SkinnedMesh, SkinnedMeshRange, SkinnedMeshVertexType,
        mem::{IndexBuffer, VertexBufferDescription, vertex::ElementName},
    },
};
use pyo3::{Py, PyRef, Python};
use rust_api::{Bone, Context, Joint, MaterialRange, Skl, Skn};

#[macro_export]
macro_rules! debug {
    ($($arg:tt)*) => {
        #[cfg(debug_assertions)] {
            println!($($arg)*);
        }
    };
}

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
        path: Option<std::path::PathBuf>,
        bones: std::collections::HashMap<String, PyRef<'_, Bone>>,
    ) -> Result<std::collections::HashMap<String, u8>, anyhow::Error> {
        let mut skl = RigResource::builder("skeleton_name", "skeleton_asset_name");

        let orig_bone_count = bones.len();
        let mut joints = bones
            .into_iter()
            .map(|(name, bone)| {
                let local_transform = glam::Mat4::from_cols_array_2d(&bone.local).transpose();
                let ibm = glam::Mat4::from_cols_array_2d(&bone.ibm).transpose();

                debug!("mat: {:?}", local_transform.to_scale_rotation_translation());
                (
                    name.clone(),
                    (
                        joint::Builder::new(name)
                            .with_local_transform(local_transform)
                            .with_inverse_bind_transform(ibm)
                            .with_influence(bone.is_influence),
                        bone.parent.clone(),
                    ),
                )
            })
            .collect::<HashMap<_, _>>();

        let mut child_map: HashMap<String, Vec<String>> = joints
            .keys()
            .map(|name| (name.to_owned(), Vec::new()))
            .collect();

        for (name, (_, parent)) in &joints {
            debug!("bone {name:?} -> {parent:?}");
            let Some(parent_map) = parent.clone().and_then(|p| child_map.get_mut(&p)) else {
                continue;
            };
            parent_map.push(name.clone());
            // skl.add_root_joint(joint.clone().with_children([joint::Builder::new("assas")]));
        }

        let mut processed = 0;
        let nodes = topological_sort(&child_map).unwrap();
        for n in nodes.iter().rev() {
            debug!("- {n}");
            let Some(children) = child_map.remove(n) else {
                continue;
            };
            let children = children
                .into_iter()
                .filter_map(|c| joints.remove(&c).map(|j| j.0))
                .collect::<Vec<_>>();
            debug!("  - {children:?}");
            let Some(joint) = joints.get_mut(n) else {
                continue;
            };
            processed += children.len();
            joint.0.add_children(children);
        }

        debug!("{processed} child bones.");
        debug!("{} root bones.", joints.len());
        if orig_bone_count != processed + joints.len() {
            debug!("[!!] we got {orig_bone_count} bones!");
        }

        for (_, joint) in joints {
            skl.add_root_joint(joint.0);
        }

        // let root_joints = bones
        //     .iter()
        //     .filter_map(|(name, bone)| match bone.parent.is_some() {
        //         true => None,
        //         false => {
        //             joints.insert(name, joint::Builder::new(name));
        //             Some(name)
        //         }
        //     })
        //     .collect::<Vec<_>>();

        // debug!("parsed {} bones", joints.len());
        // if orig_bone_count != joints.len() {
        //     debug!("[!!] we got {orig_bone_count} bones!");
        // }

        let rig = skl.build();
        if let Some(path) = path {
            let mut file = std::fs::File::create(path).map(BufWriter::new).unwrap();
            rig.to_writer(&mut file).unwrap();
        }

        let joint_map = rig
            .influences()
            .iter()
            .copied()
            .enumerate()
            .map(|(i, joint_idx)| (rig.joints()[joint_idx as usize].name().to_string(), i as _))
            .collect();
        Ok(joint_map)
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
        let mut vert_buf = Vec::new();
        let vertex_count = vertex_positions.len() / 3;
        for i in 0..vertex_count {
            vert_buf.extend(
                vertex_positions[(i * 3)..(i * 3) + 3]
                    .iter()
                    .flat_map(|n| n.to_le_bytes()),
            );
            vert_buf.extend_from_slice(&vertex_blend_indices[i * 4..i * 4 + 4]);
            vert_buf.extend(
                vertex_blend_weights[i * 4..i * 4 + 4]
                    .iter()
                    .flat_map(|w| w.to_le_bytes()),
            );
            vert_buf.extend(
                vertex_normals[i * 3..i * 3 + 3]
                    .iter()
                    .flat_map(|n| n.to_le_bytes()),
            );
            vert_buf.extend([0_u8; 8]); // TEXCOORD_0
        }

        let vert_buf = VertexBufferDescription::from(SkinnedMeshVertexType::Basic)
            .into_vertex_buffer(vert_buf);

        let mut idx_buf = Vec::new();

        for tri in triangles {
            idx_buf.extend((*tri as u16).to_le_bytes());
        }

        let idx_count = idx_buf.len();
        let idx_buf = IndexBuffer::<u16>::new(idx_buf);

        let skn = SkinnedMesh::new(
            vec![SkinnedMeshRange::new(
                // FIXME
                "ashe_base_2011_MD_lambert2SG1",
                0,
                vertex_count as _,
                0,
                idx_count as _,
            )],
            vert_buf,
            idx_buf,
        );
        let mut file = std::fs::File::create(path).map(BufWriter::new).unwrap();
        skn.to_writer(&mut file).unwrap();

        Ok(())
    }
}

fn topological_sort(graph: &HashMap<String, Vec<String>>) -> Option<Vec<String>> {
    let mut in_degree: HashMap<String, usize> = HashMap::new();
    let mut zero_in_degree_queue: VecDeque<String> = VecDeque::new();
    let mut sorted_list: Vec<String> = Vec::new();

    // Initialize in-degree of all nodes to 0
    for node in graph.keys() {
        in_degree.insert(node.clone(), 0);
    }

    // Calculate in-degree of each node
    for children in graph.values() {
        for child in children {
            if let Some(degree) = in_degree.get_mut(child) {
                *degree += 1;
            }
        }
    }

    // Collect nodes with zero in-degree
    for (node, &degree) in in_degree.iter() {
        if degree == 0 {
            zero_in_degree_queue.push_back(node.clone());
        }
    }

    // Process nodes with zero in-degree
    while let Some(node) = zero_in_degree_queue.pop_front() {
        sorted_list.push(node.clone());

        if let Some(children) = graph.get(&node) {
            for child in children {
                if let Some(degree) = in_degree.get_mut(child) {
                    *degree -= 1;
                    if *degree == 0 {
                        zero_in_degree_queue.push_back(child.clone());
                    }
                }
            }
        }
    }

    // If sorted list contains all nodes, return it, otherwise there's a cycle
    if sorted_list.len() == graph.len() {
        Some(sorted_list)
    } else {
        None
    }
}

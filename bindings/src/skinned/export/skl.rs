use lib::core::animation::{joint, RigResource};
use pyo3::prelude::*;
use std::{
    collections::{HashMap, VecDeque},
    io::BufWriter,
    path::PathBuf,
};

use super::Bone;
use crate::debug;

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

#[pyfunction]
pub fn export_skl(
    bones: HashMap<String, PyRef<'_, Bone>>,
    path: Option<PathBuf>,
) -> PyResult<HashMap<String, u8>> {
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
    debug!("joint_map: {joint_map:?}");
    Ok(joint_map)
}

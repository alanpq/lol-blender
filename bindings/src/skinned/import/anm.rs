use glam::{Quat, Vec3};
use itertools::Itertools;
use lib::core::animation::{
    asset::{CompressedTime, FrameValue, TimedValue},
    AnimationAsset, RigResource,
};
use pyo3::prelude::*;
use std::{collections::HashMap, fs::File, io::BufReader, path::PathBuf};

use crate::{skinned::export::Bone, Mat4};

#[pyclass]
pub struct Anm {
    #[pyo3(get)]
    pub joint_anms: HashMap<u32, [Vec<f32>; 10]>,
    #[pyo3(get)]
    pub fps: f32,
}

#[pyfunction]
pub fn import_anm(py: Python<'_>, path: PathBuf) -> PyResult<Anm> {
    let mut file = File::open(path).map(BufReader::new).unwrap();
    let AnimationAsset::Compressed(anm) = AnimationAsset::from_reader(&mut file).unwrap() else {
        panic!("uncompressed animations not supported");
    };

    let axis_convert = glam::Mat4::from_cols_array(&[
        1.0, 0.0, 0.0, 0.0, -0.0, 0.0, -1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0,
    ]);

    let rotation_convert = glam::Mat4::from_cols_array(&[
        0.0, -1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0,
    ])
    .transpose();

    let mut joint_anms = HashMap::<u32, [Vec<f32>; 10]>::new();
    let mut frames = anm.frames().collect_vec();
    for frame in &mut frames {
        // order is `XYZ XYZW XYZ`
        //           loc rot scale
        let (time, components, off) = match &mut frame.value {
            FrameValue::Translation(v) => {
                v.value = axis_convert.transform_vector3(v.value);
                (v.time, &v.value.to_array()[..], 0)
                //(v.time, &Vec3::ZERO.to_array()[..], 0)
            }
            FrameValue::Rotation(v) => {
                //continue;
                (
                    v.time,
                    &Quat::from_xyzw(-v.value.w, -v.value.x, v.value.y, v.value.z).to_array()[..],
                    3,
                )
            }
            FrameValue::Scale(v) => {
                //v.value = axis_convert.transform_vector3(v.value);
                (v.time, &Vec3::ONE.to_array()[..], 7)
                //(v.time, &v.value.to_array()[..], 7)
            }
        };

        dbg!(frame.joint);
        let joint_id = anm
            .joints
            .get(frame.joint as usize)
            .expect("frame joint id to be in anm joint list");
        let joint_components = joint_anms.entry(*joint_id).or_default();
        for (i, c) in components.iter().enumerate() {
            joint_components[i + off].push((time * anm.fps * 2.0) + 1.0);
            joint_components[i + off].push(*c);
        }
    }

    Ok(Anm {
        joint_anms,
        fps: anm.fps,
    })
}

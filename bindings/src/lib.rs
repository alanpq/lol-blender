use lib::core::animation::{joint, RigResource};
use lib::core::mem::{
    IndexBuffer, IndexFormat, VertexBuffer, VertexBufferDescription, VertexBufferUsage,
    VertexElement,
};
use lib::core::mesh::{SkinnedMesh, SkinnedMeshVertexType};
use pyo3::prelude::*;
use std::collections::{HashMap, VecDeque};
use std::io::BufWriter;
use std::path::PathBuf;

#[pyfunction]
fn version() -> PyResult<&'static str> {
    Ok("1.0.2")
}

type Vec3 = [f32; 3];

#[derive(Debug)]
#[pyclass]
struct Vertex {
    #[pyo3(get, set)]
    pos: Vec3,
    #[pyo3(get, set)]
    normal: Vec3,
}

#[pymethods]
impl Vertex {
    #[new]
    fn py_new(pos: Vec3, normal: Vec3) -> Self {
        Self { pos, normal }
    }
}

impl Vertex {
    fn push_bytes(&self, v: &mut Vec<u8>) {
        // 52 total
        for i in self.pos {
            // POSITION (12)
            v.extend_from_slice(&i.to_le_bytes())
        }
        v.extend([0_u8; 4]); // BLEND_INDEX (4)
        v.extend([0_u8; 16]); // BLEND_WEIGHT (16)

        for i in self.normal {
            // NORMAL (12)
            v.extend_from_slice(&i.to_le_bytes())
        }
        v.extend([0_u8; 8]); // TEXCOORD_0 (8)
    }
}

#[pyfunction]
fn export_skn(
    path: PathBuf,
    vertices: Vec<PyRef<'_, Vertex>>,
    triangles: Vec<[i64; 3]>,
) -> PyResult<()> {
    // println!("ve!rts: {vertices:?}");

    let mut buf = Vec::new();
    for v in vertices {
        v.push_bytes(&mut buf);
    }
    // println!("{buf:?}");
    let vert_buf =
        VertexBufferDescription::from(SkinnedMeshVertexType::Basic).into_vertex_buffer(buf);
    // println!("{vert_buf:?}");
    let mut buf = Vec::new();

    for tri in triangles {
        for i in tri {
            buf.extend((i as u16).to_le_bytes());
        }
    }

    let idx_buf = IndexBuffer::new(IndexFormat::U16, buf);

    let skn = SkinnedMesh::new(vec![], vert_buf, idx_buf);
    let mut file = std::fs::File::create(path).map(BufWriter::new).unwrap();
    skn.to_writer(&mut file).unwrap();

    Ok(())
}

#[derive(Debug)]
#[pyclass]
struct Bone {
    #[pyo3(get, set)]
    parent: Option<String>,
}

#[pymethods]
impl Bone {
    #[new]
    fn py_new(parent: String) -> Self {
        Self {
            parent: match parent.is_empty() {
                true => None,
                false => Some(parent),
            },
        }
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

#[pyfunction]
fn export_skl(path: PathBuf, bones: HashMap<String, PyRef<'_, Bone>>) -> PyResult<()> {
    let mut skl = RigResource::builder("skeleton_name", "skeleton_asset_name");

    let orig_bone_count = bones.len();
    let mut joints = bones
        .into_iter()
        .map(|(name, bone)| {
            (
                name.clone(),
                (joint::Builder::new(name), bone.parent.clone()),
            )
        })
        .collect::<HashMap<_, _>>();

    let mut child_map: HashMap<String, Vec<String>> = joints
        .keys()
        .map(|name| (name.to_owned(), Vec::new()))
        .collect();

    for (name, (joint, parent)) in &joints {
        println!("bone {name:?} -> {parent:?}");
        let Some(parent_map) = parent.clone().and_then(|p| child_map.get_mut(&p)) else {
            continue;
        };
        parent_map.push(name.clone());
        // skl.add_root_joint(joint.clone().with_children([joint::Builder::new("assas")]));
    }

    let mut processed = 0;
    let nodes = topological_sort(&child_map).unwrap();
    for n in nodes.iter().rev() {
        println!("- {n}");
        let Some(children) = child_map.remove(n) else {
            continue;
        };
        let children = children
            .into_iter()
            .filter_map(|c| joints.remove(&c).map(|j| j.0))
            .collect::<Vec<_>>();
        println!("  - {children:?}");
        let Some(joint) = joints.get_mut(n) else {
            continue;
        };
        processed += children.len();
        joint.0.add_children(children);
    }

    println!("{processed} child bones.");
    println!("{} root bones.", joints.len());
    if orig_bone_count != processed + joints.len() {
        println!("[!!] we got {orig_bone_count} bones!");
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

    // println!("parsed {} bones", joints.len());
    // if orig_bone_count != joints.len() {
    //     println!("[!!] we got {orig_bone_count} bones!");
    // }

    let mut file = std::fs::File::create(path).map(BufWriter::new).unwrap();

    skl.build().to_writer(&mut file).unwrap();

    Ok(())
}

#[pymodule]
fn league_toolkit(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<Vertex>()?;
    m.add_class::<Bone>()?;
    m.add_function(wrap_pyfunction!(version, m)?)?;
    m.add_function(wrap_pyfunction!(export_skn, m)?)?;
    m.add_function(wrap_pyfunction!(export_skl, m)?)?;
    Ok(())
}

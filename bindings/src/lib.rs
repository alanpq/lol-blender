use std::io::BufWriter;
use std::path::PathBuf;
use lib::core::mem::{IndexBuffer, IndexFormat, VertexBuffer, VertexBufferDescription, VertexBufferUsage, VertexElement};
use pyo3::prelude::*;
use lib::core::mesh::{SkinnedMesh, SkinnedMeshVertexType};

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
        for i in self.pos { // POSITION (12)
            v.extend_from_slice(&i.to_le_bytes())
        }
        v.extend([0_u8; 4]); // BLEND_INDEX (4)
        v.extend([0_u8; 16]); // BLEND_WEIGHT (16)

        for i in self.normal { // NORMAL (12)
            v.extend_from_slice(&i.to_le_bytes())
        }
        v.extend([0_u8; 8]); // TEXCOORD_0 (8)
    }
}

#[pyfunction]
fn export_skn(path: PathBuf, vertices: Vec<PyRef<'_, Vertex>>, triangles: Vec<[i64; 3]>) -> PyResult<()> {
    println!("ve!rts: {vertices:?}");

    let mut buf = Vec::new();
    for v in vertices {
        v.push_bytes(&mut buf);
    }
    println!("{buf:?}");
    let vert_buf = VertexBufferDescription::from(SkinnedMeshVertexType::Basic).into_vertex_buffer(
        buf
    );
    println!("{vert_buf:?}");
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

#[pymodule]
fn league_toolkit(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<Vertex>()?;
    m.add_function(wrap_pyfunction!(version, m)?)?;
    m.add_function(wrap_pyfunction!(export_skn, m)?)?;
    Ok(())
}
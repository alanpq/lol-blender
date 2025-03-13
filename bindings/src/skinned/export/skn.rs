use super::Vertex;
use lib::core::{
    mem::{IndexBuffer, IndexFormat, VertexBufferDescription},
    mesh::{SkinnedMesh, SkinnedMeshRange, SkinnedMeshVertexType},
};
use pyo3::prelude::*;
use std::{io::BufWriter, path::PathBuf};

#[pyfunction]
pub fn export_skn(
    path: PathBuf,
    vertices: Vec<PyRef<'_, Vertex>>,
    triangles: Vec<[i64; 3]>,
    influences: Option<Vec<[(i16, f32); 4]>>,
) -> PyResult<()> {
    let mut buf = Vec::new();
    let vertex_count = vertices.len();
    for v in vertices {
        v.push_bytes(&mut buf);
    }

    // debug!("{buf:?}");
    let vert_buf =
        VertexBufferDescription::from(SkinnedMeshVertexType::Basic).into_vertex_buffer(buf);
    // debug!("{vert_buf:?}");
    let mut buf = Vec::new();

    for tri in triangles {
        for i in tri {
            buf.extend((i as u16).to_le_bytes());
        }
    }

    let idx_count = buf.len();
    let idx_buf = IndexBuffer::new(IndexFormat::U16, buf);

    let skn = SkinnedMesh::new(
        vec![SkinnedMeshRange::new(
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

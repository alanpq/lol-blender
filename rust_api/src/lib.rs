use std::{collections::HashMap, path::PathBuf};



#[derive(Debug)]
pub struct Skl {
    pub joints: Vec<()>,

    pub influence_lookup: HashMap<i16, String>,
}

pub trait Context: Send + Sync {
    fn sample_inside(&self, flat_vertices: &[f32], flat_triangles: &[i32]) -> Vec<f32>;
    fn import_skl(&self, path: PathBuf) -> Skl;
}

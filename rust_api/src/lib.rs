pub trait Context: Send + Sync {
    fn sample_inside(&self, flat_vertices: &[f32], flat_triangles: &[i32]) -> Vec<f32>;
}

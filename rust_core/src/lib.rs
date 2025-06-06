use nalgebra::{Matrix3, Vector3};
use rust_api::Context;

pub struct Impl;
impl Context for Impl {
    fn sample_inside(&self, flat_vertices: &[f32], flat_triangles: &[i32]) -> Vec<f32> {
        let vertices = flat_vertices
            .chunks_exact(3)
            .map(Vector3::from_column_slice)
            .collect::<Vec<_>>();
        let triangles = flat_triangles
            .chunks_exact(3)
            .map(|chunk| [chunk[0], chunk[1], chunk[2]])
            .collect::<Vec<_>>();

        let to_positions = |[a, b, c]: &[i32; 3]| {
            [
                vertices[*a as usize],
                vertices[*b as usize],
                vertices[*c as usize],
            ]
        };

        let wind_triangle = |position: &Vector3<f32>, triangle: &[i32; 3]| {
            let [a, b, c]: [Vector3<f32>; 3] = to_positions(triangle).map(|x| x - position);

            let ab = a.dot(&b);
            let bc = b.dot(&c);
            let ca = c.dot(&a);

            let det_abc = Matrix3::from_columns(&[a, b, c]).determinant();

            let a = a.norm();
            let b = b.norm();
            let c = c.norm();

            let divisor = a * b * c + ab * c + bc * a + ca * b;

            det_abc.atan2(divisor) / std::f32::consts::TAU
        };

        let is_inside = |sample: &Vector3<f32>| {
            triangles
                .iter()
                .map(|triangle| wind_triangle(sample, triangle))
                .sum::<f32>()
                > 0.8
        };

        let mut aabb = Aabb::new(vertices.iter());
        aabb.min += Vector3::repeat(0.01);
        aabb.max -= Vector3::repeat(0.01);
        aabb.lattice(0.1)
            .filter(is_inside)
            .flat_map(Vector3::flat)
            .collect()
    }
}

trait Flat {
    fn flat(self) -> [f32; 3];
}

impl Flat for Vector3<f32> {
    fn flat(self) -> [f32; 3] {
        [self.x, self.y, self.z]
    }
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Aabb {
    pub min: Vector3<f32>,
    pub max: Vector3<f32>,
}

impl Default for Aabb {
    fn default() -> Self {
        Self {
            min: Vector3::repeat(f32::MAX),
            max: Vector3::repeat(f32::MIN),
        }
    }
}

impl Aabb {
    pub fn new<'a>(points: impl Iterator<Item = &'a Vector3<f32>>) -> Self {
        points.fold(Default::default(), |Self { min, max }, point| Self {
            min: min.inf(point),
            max: max.sup(point),
        })
    }

    pub fn extents(&self) -> Vector3<f32> {
        self.max - self.min
    }

    pub fn lattice(&self, spacing: f32) -> impl Iterator<Item = Vector3<f32>> {
        let n = (self.extents() / spacing).map(|x| x.max(1.) as usize);
        (0..=n.x).flat_map(move |i| {
            (0..=n.y).flat_map(move |j| {
                (0..=n.z).map(move |k| {
                    self.min
                        + self.extents().component_mul(&Vector3::new(
                            i as f32 / n.x as f32,
                            j as f32 / n.y as f32,
                            k as f32 / n.z as f32,
                        ))
                })
            })
        })
    }
}

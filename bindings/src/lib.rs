use lib::core::animation::{joint, RigResource};
use pyo3::prelude::*;
use std::collections::{HashMap, VecDeque};
use std::io::BufWriter;
use std::path::PathBuf;

pub mod skinned;

#[pyfunction]
fn version() -> PyResult<&'static str> {
    Ok("1.0.2")
}

pub type Vec3 = [f32; 3];
pub type Vec4 = [f32; 4];
pub type Mat4 = [[f32; 4]; 4];

#[macro_export]
macro_rules! debug {
    ($($arg:tt)*) => {
        #[cfg(debug_assertions)] {
            println!($($arg)*);
        }
    };
}

#[pymodule]
fn league_toolkit(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(version, m)?)?;

    skinned::export::register(m)?;
    Ok(())
}

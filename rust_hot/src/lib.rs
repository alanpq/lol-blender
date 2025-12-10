pub use rust_api::Context;
use rust_core::Impl;

pub use rust_api;

#[unsafe(no_mangle)]
pub fn create_context() -> Box<dyn Context> {
    println!("creating new rust context");
    Box::new(Impl)
}

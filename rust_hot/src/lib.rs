pub use rust_api::Context;
use rust_core::Impl;

#[unsafe(no_mangle)]
pub fn create_context() -> Box<dyn Context> {
    println!("creating new rust context");
    Box::new(Impl)
}

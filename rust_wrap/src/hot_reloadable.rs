use anyhow::{Context, Result};
use lazy_static::lazy_static;
use std::sync::Mutex;
use std::thread::spawn;

#[cfg(not(feature = "hot_reload"))]
pub use rust_hot as rust_hot_reload;
#[cfg(feature = "hot_reload")]
#[cfg_attr(
    debug_assertions,
    hot_lib_reloader::hot_module(
        dylib = "rust_hot",
        lib_dir = concat!(env!("CARGO_MANIFEST_DIR"), "/../rust_hot/target/debug")
    )
)]
#[cfg_attr(
    not(debug_assertions),
    hot_lib_reloader::hot_module(
        dylib = "rust_hot",
        lib_dir = concat!(env!("CARGO_MANIFEST_DIR"), "/../rust_hot/target/release")
    )
)]
pub mod rust_hot_reload {
    hot_functions_from_file!("../rust_hot/src/lib.rs");

    #[allow(unused)]
    pub use rust_hot::*;

    #[lib_change_subscription]
    pub fn subscribe() -> hot_lib_reloader::LibReloadObserver {}
}

lazy_static! {
    static ref LOCK: Mutex<Option<Box<dyn rust_hot_reload::Context>>> =
        Mutex::new(Default::default());
}

pub fn initialize() {
    *LOCK.lock().unwrap() = Some(rust_hot_reload::create_context());
}

pub fn try_with_context<R, F: FnOnce(&mut dyn rust_hot_reload::Context) -> Result<R>>(
    f: F,
) -> Result<R> {
    f(LOCK
        .lock()
        .unwrap()
        .as_mut()
        .context("no context")?
        .as_mut())
}

pub fn with_context<R, F: FnOnce(&mut dyn rust_hot_reload::Context) -> R>(f: F) -> Result<R> {
    try_with_context(|c| Ok(f(c)))
}

#[cfg(feature = "hot_reload")]
pub fn handle_reload() {
    let _ = spawn(|| {
        let lib_observer = rust_hot_reload::subscribe();
        loop {
            // wait for reload and block it
            let update_blocker = lib_observer.wait_for_about_to_reload();

            // wait for any library calls to finish and block further calls
            let mut context_guard = LOCK.lock().unwrap();

            // cleanup
            let context = context_guard.take();

            // this should block until any threads are joined and any resources are dropped
            drop(context);

            // let the library update commence and wait until it's finished
            drop(update_blocker);
            lib_observer.wait_for_reload();

            // fresh context with new lib version
            *context_guard = Some(rust_hot_reload::create_context());

            // context_guard is dropped and calls can continue
        }
    });
}

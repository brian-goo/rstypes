use pyo3::prelude::*;

mod rtype;
pub use rtype::{rcache::RCacheMap, rmap::RMap};

#[pymodule(name = "rstypes")]
mod _rtype {

    #[pymodule_export]
    use crate::{RCacheMap, RMap};
}

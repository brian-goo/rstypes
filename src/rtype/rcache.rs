use std::sync::Arc;
use std::time::{Duration, Instant};

use indexmap::{map::Entry, IndexMap};
use pyo3::prelude::*;
use tokio::sync::Mutex;

use crate::rtype::rmap::{try_into_key, Key};

#[pyclass]
pub struct RCacheMap {
    map: Arc<Mutex<IndexMap<Key, (Instant, PyObject)>>>,
}

#[pymethods]
impl RCacheMap {
    #[new]
    fn new() -> Self {
        Self {
            map: Arc::new(Mutex::new(IndexMap::new())),
        }
    }

    fn set<'a>(&self, py: Python<'a>, key: PyObject, value: PyObject, ttl: f64) -> PyResult<Bound<'a, PyAny>> {
        let key = try_into_key(key, py)?;
        let map = self.map.clone();
        pyo3_async_runtimes::tokio::future_into_py(py, async move {
            let mut locked = map.lock().await;
            let exp = Instant::now() + Duration::from_secs_f64(ttl);
            locked.insert(key, (exp, value));
            Python::with_gil(|py| Ok(py.None()))
        })
    }

    fn get<'a>(&self, py: Python<'a>, key: PyObject) -> PyResult<Bound<'a, PyAny>> {
        let key = try_into_key(key, py)?;
        let map = self.map.clone();

        pyo3_async_runtimes::tokio::future_into_py(py, async move {
            let mut locked = map.lock().await;
            Python::with_gil(|py| match locked.entry(key) {
                Entry::Occupied(entry) => {
                    let (exp, value) = entry.get();
                    if Instant::now() >= *exp {
                        entry.swap_remove();
                        Ok(py.None())
                    } else {
                        Ok(value.clone_ref(py))
                    }
                }
                Entry::Vacant(_) => Ok(py.None()),
            })
        })
    }

    /// No trait for this with RMap's pop since it seems we cannot implement it cleanly
    /// due to different base struct etc
    fn pop<'a>(&self, py: Python<'a>, key: PyObject) -> PyResult<Bound<'a, PyAny>> {
        let key = try_into_key(key, py)?;
        let map = self.map.clone();
        pyo3_async_runtimes::tokio::future_into_py(py, async move {
            let mut locked = map.lock().await;
            locked.swap_remove(&key);
            Python::with_gil(|py| Ok(py.None()))
        })
    }

    fn pop_expired<'a>(&self, py: Python<'a>) -> PyResult<Bound<'a, PyAny>> {
        let map = self.map.clone();
        pyo3_async_runtimes::tokio::future_into_py(py, async move {
            let mut locked = map.lock().await;
            let now = Instant::now();
            locked.retain(|_, (exp, _)| *exp > now);
            Python::with_gil(|py| Ok(py.None()))
        })
    }
}

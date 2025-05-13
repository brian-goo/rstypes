use std::sync::Arc;

use indexmap::{map::Entry, IndexMap};
use pyo3::prelude::*;
use tokio::sync::Mutex;

#[derive(Hash, Eq, PartialEq, Clone, Debug)]
pub enum Key {
    Int(i64),
    Str(String),
}

pub fn try_into_key(key: PyObject, py: Python<'_>) -> PyResult<Key> {
    if let Ok(i) = key.extract::<i64>(py) {
        Ok(Key::Int(i))
    } else if let Ok(s) = key.extract::<String>(py) {
        Ok(Key::Str(s))
    } else {
        Err(PyErr::new::<pyo3::exceptions::PyTypeError, _>("Key must be int or str"))
    }
}

#[pyclass]
pub struct RMap {
    map: Arc<Mutex<IndexMap<Key, PyObject>>>,
    factory: Option<PyObject>, // PyObject: python callable
}

#[pymethods]
impl RMap {
    #[new]
    #[pyo3(signature = (factory=None))]
    fn new(factory: Option<PyObject>) -> Self {
        Self {
            map: Arc::new(Mutex::new(IndexMap::new())),
            factory,
        }
    }

    fn set<'a>(&self, py: Python<'a>, key: PyObject, value: PyObject) -> PyResult<Bound<'a, PyAny>> {
        let key = try_into_key(key, py)?;
        let map = self.map.clone();
        pyo3_async_runtimes::tokio::future_into_py(py, async move {
            let mut locked = map.lock().await;
            locked.insert(key, value);
            Python::with_gil(|py| Ok(py.None()))
        })
    }

    fn pop<'a>(&self, py: Python<'a>, key: PyObject) -> PyResult<Bound<'a, PyAny>> {
        let key = try_into_key(key, py)?;
        let map = self.map.clone();
        pyo3_async_runtimes::tokio::future_into_py(py, async move {
            let mut locked = map.lock().await;
            locked.swap_remove(&key);
            Python::with_gil(|py| Ok(py.None()))
        })
    }

    fn get<'a>(&self, py: Python<'a>, key: PyObject) -> PyResult<Bound<'a, PyAny>> {
        let key = try_into_key(key, py)?;
        let map = self.map.clone();
        let factory = self.factory.as_ref().map(|f| f.clone_ref(py));

        pyo3_async_runtimes::tokio::future_into_py(py, async move {
            let mut locked = map.lock().await;
            Python::with_gil(|py| match locked.entry(key) {
                Entry::Occupied(entry) => Ok(entry.get().clone_ref(py)),
                Entry::Vacant(entry) => {
                    if let Some(factory) = &factory {
                        let default = factory.call0(py)?;
                        entry.insert(default.clone_ref(py));
                        Ok(default)
                    } else {
                        Ok(py.None())
                    }
                }
            })
        })
    }
}

c:
	maturin build --release

p:
	pip install --force-reinstall ./target/wheels/*.whl

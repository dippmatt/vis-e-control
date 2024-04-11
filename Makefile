# Make target that downloads the dataset from E-Control website
# Launch the python program that downloads the dataset from E-Control website

PYTHON_ENV ?= venv/bin/python3

make download:
	$(PYTHON_ENV) src/download_dataset.py

make init_venv:
	python3 -m venv venv
	venv/bin/pip install -r requirements.txt
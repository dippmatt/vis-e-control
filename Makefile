PYTHON_ENV ?= venv/bin/python3

default:
	@echo "Please specify a target"

download:
	$(PYTHON_ENV) src/download_dataset.py

init_venv:
	python3 -m venv venv
	venv/bin/pip install -r requirements.txt

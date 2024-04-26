PYTHON_ENV ?= venv/bin/python3

default:
	@echo "Please specify a target"

init_venv:
	python3 -m venv venv
	venv/bin/pip install -r requirements.txt
	git submodule update --init --recursive

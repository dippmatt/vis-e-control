PYTHON_ENV ?= venv/bin/python3

default:
	@echo "Please specify a target"

init_env:
	python3 -m venv venv
	venv/bin/pip install -r requirements.txt
	git submodule update --init --recursive

process_data:
	$(PYTHON_ENV) src/anlagenregister.py

run_app:
	$(PYTHON_ENV) src/dash_app.py
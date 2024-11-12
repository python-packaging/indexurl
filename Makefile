PYTHON?=python
SOURCES=indexurl setup.py
UV?=uv

.PHONY: venv
venv:
	$(UV) venv .venv
	source .venv/bin/activate && make setup
	@echo 'run `source .venv/bin/activate` to use virtualenv'

# The rest of these are intended to be run within the venv, where python points
# to whatever was used to set up the venv.

.PHONY: setup
setup:
	uv pip install -e .[dev,test]

.PHONY: test
test:
	python -m coverage run -m indexurl.tests $(TESTOPTS)
	python -m coverage report

.PHONY: format
format:
	python -m ufmt format $(SOURCES)

.PHONY: lint
lint:
	python -m ufmt check $(SOURCES)
	python -m flake8 $(SOURCES)
	python -m checkdeps --allow-names indexurl indexurl
	mypy --strict --install-types --non-interactive indexurl

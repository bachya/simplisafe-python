clean:
	.venv/bin/pre-commit uninstall
	rm -rf .venv/
coverage:
	.venv/bin/py.test -s --verbose --cov-report term-missing --cov-report xml --cov=simplipy tests
format:
	.venv/bin/black simplipy
	.venv/bin/black tests
	.venv/bin/docformatter -ir simplipy
init:
	python3 -m venv .venv
	.venv/bin/pip3 install poetry
	.venv/bin/poetry lock
	.venv/bin/poetry install
	.venv/bin/pre-commit install
lint:
	.venv/bin/black --check --fast simplipy
	.venv/bin/flake8 simplipy
	.venv/bin/docformatter -r -c simplipy
	.venv/bin/pylint simplipy
publish:
	.venv/bin/poetry build
	.venv/bin/poetry publish
	rm -rf dist/ build/ .egg *.egg-info/
test:
	.venv/bin/py.test
typing:
	.venv/bin/mypy --ignore-missing-imports simplipy

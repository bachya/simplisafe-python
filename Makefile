coverage:
	pipenv run py.test -s --verbose --cov-report term-missing --cov-report xml --cov=simplipy tests
init:
	pip install pip==18.0 pipenv
	pipenv lock
	pipenv install --dev
lint:
	pipenv run flake8 simplipy
	pipenv run pydocstyle simplipy
	pipenv run pylint simplipy
publish:
	pipenv run python setup.py sdist bdist_wheel
	pipenv run twine upload dist/*
	rm -rf dist/ build/ .egg simplisafe_python.egg-info/
test:
	pipenv run py.test
typing:
	pipenv run mypy --ignore-missing-imports simplipy

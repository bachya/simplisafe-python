ci:
	pipenv run py.test --junitxml=report.xml
coverage:
	pipenv run py.test -s --verbose --cov-report term-missing --cov-report xml --cov=simplipy tests
init:
	pip install --upgrade pip pipenv
	pipenv lock
	pipenv install --dev
lint:
	pipenv run flake8 simplisafe-python
	pipenv run pydocstyle simplisafe-python
publish:
	python setup.py sdist bdist_wheel
	pipenv run twine upload dist/*
	rm -rf dist/ build/ .egg simplisafe-python.egg-info/

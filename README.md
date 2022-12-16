# 🚨 simplisafe-python: A Python3, async interface to the SimpliSafe™ API

[![CI][ci-badge]][ci]
[![PyPI][pypi-badge]][pypi]
[![Version][version-badge]][version]
[![License][license-badge]][license]
[![Code Coverage][codecov-badge]][codecov]
[![Maintainability][maintainability-badge]][maintainability]

<a href="https://www.buymeacoffee.com/bachya1208P" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>

`simplisafe-python` (hereafter referred to as `simplipy`) is a Python3,
`asyncio`-driven interface to the unofficial [SimpliSafe™][simplisafe] API. With it,
users can get data on their system (including available sensors), set the system state,
and more.

# Documentation

You can find complete documentation [here][docs].

# Contributing

Thanks to all of [our contributors][contributors] so far!

1. [Check for open features/bugs][issues] or [initiate a discussion on one][new-issue].
2. [Fork the repository][fork].
3. (_optional, but highly recommended_) Create a virtual environment: `python3 -m venv .venv`
4. (_optional, but highly recommended_) Enter the virtual environment: `source ./.venv/bin/activate`
5. Install the dev environment: `script/setup`
6. Code your new feature or bug fix on a new branch.
7. Write tests that cover your new functionality.
8. Run tests and ensure 100% code coverage: `poetry run pytest --cov simplisafe-python tests`
9. Update `README.md` with any new documentation.
10. Submit a pull request!

[ci-badge]: https://github.com/bachya/simplisafe-python/workflows/CI/badge.svg
[ci]: https://github.com/bachya/simplisafe-python/actions
[codecov-badge]: https://codecov.io/gh/bachya/simplisafe-python/branch/dev/graph/badge.svg
[codecov]: https://codecov.io/gh/bachya/simplisafe-python
[contributors]: https://github.com/bachya/simplisafe-python/graphs/contributors
[docs]: https://simplisafe-python.readthedocs.io
[fork]: https://github.com/bachya/simplisafe-python/fork
[issues]: https://github.com/bachya/simplisafe-python/issues
[license-badge]: https://img.shields.io/pypi/l/simplisafe-python.svg
[license]: https://github.com/bachya/simplisafe-python/blob/main/LICENSE
[maintainability-badge]: https://api.codeclimate.com/v1/badges/f46d8b1dcfde6a2f683d/maintainability
[maintainability]: https://codeclimate.com/github/bachya/simplisafe-python/maintainability
[new-issue]: https://github.com/bachya/simplisafe-python/issues/new
[pypi-badge]: https://img.shields.io/pypi/v/simplisafe-python.svg
[pypi]: https://pypi.python.org/pypi/simplisafe-python
[simplisafe]: https://simplisafe.com
[version-badge]: https://img.shields.io/pypi/pyversions/simplisafe-python.svg
[version]: https://pypi.python.org/pypi/simplisafe-python

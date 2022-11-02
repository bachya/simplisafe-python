# 🚨 simplisafe-python: A Python3, async interface to the SimpliSafe™ API

[![CI](https://github.com/bachya/simplisafe-python/workflows/CI/badge.svg)](https://github.com/bachya/simplisafe-python/actions)
[![PyPi](https://img.shields.io/pypi/v/simplisafe-python.svg)](https://pypi.python.org/pypi/simplisafe-python)
[![Version](https://img.shields.io/pypi/pyversions/simplisafe-python.svg)](https://pypi.python.org/pypi/simplisafe-python)
[![License](https://img.shields.io/pypi/l/simplisafe-python.svg)](https://github.com/bachya/simplisafe-python/blob/main/LICENSE)
[![Code Coverage](https://codecov.io/gh/bachya/simplisafe-python/branch/dev/graph/badge.svg)](https://codecov.io/gh/bachya/simplisafe-python)
[![Maintainability](https://api.codeclimate.com/v1/badges/f46d8b1dcfde6a2f683d/maintainability)](https://codeclimate.com/github/bachya/simplisafe-python/maintainability)
[![Say Thanks](https://img.shields.io/badge/SayThanks-!-1EAEDB.svg)](https://saythanks.io/to/bachya)

<a href="https://www.buymeacoffee.com/bachya1208P" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>

`simplisafe-python` (hereafter referred to as `simplipy`) is a Python3,
`asyncio`-driven interface to the unofficial SimpliSafe™ API. With it, users can
get data on their system (including available sensors), set the system state,
and more.

# Documentation

You can find complete documentation here: https://simplisafe-python.readthedocs.io

# Contributing

1. [Check for open features/bugs](https://github.com/bachya/simplisafe-python/issues)
   or [initiate a discussion on one](https://github.com/bachya/simplisafe-python/issues/new).
2. [Fork the repository](https://github.com/bachya/simplisafe-python/fork).
3. (_optional, but highly recommended_) Create a virtual environment: `python3 -m venv .venv`
4. (_optional, but highly recommended_) Enter the virtual environment: `source ./.venv/bin/activate`
5. Install the dev environment: `script/setup`
6. Code your new feature or bug fix.
7. Write tests that cover your new functionality.
8. Run tests and ensure 100% code coverage: `poetry run pytest --cov simplipy tests`
9. Update `README.md` with any new documentation.
10. Add yourself to `AUTHORS.md`.
11. Submit a pull request!

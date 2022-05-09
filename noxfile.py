"""Define nox actions."""
import tempfile
from typing import Any

import nox


def install_with_constraints(session: nox.sessions.Session, *args: str, **kwargs: Any):
    """Install PyPI packages based on pyproject.toml constraints."""
    with tempfile.NamedTemporaryFile() as requirements:
        session.run(
            "poetry",
            "export",
            "--dev",
            "--without-hashes",
            "--format=requirements.txt",
            f"--output={requirements.name}",
            external=True,
        )
        session.install(f"--constraint={requirements.name}", *args, **kwargs)


@nox.session
def coverage(session: nox.sessions.Session) -> None:
    """Run all tests."""
    args = session.posargs or [
        "-s",
        "--cov=simplipy",
        "--cov-report=term-missing",
        "--cov-report=xml",
    ]
    session.run("poetry", "install", "--no-dev", external=True)
    install_with_constraints(
        session, "aresponses", "pytest", "pytest-aiohttp", "pytest-cov"
    )
    session.run("pytest", *args)


@nox.session
def docs(session: nox.sessions.Session) -> None:
    """Generate a local copy of the docs."""
    session.run("poetry", "install", "--no-dev", external=True)
    install_with_constraints(session, "myst-parser", "Sphinx", "sphinx-rtd-theme")
    session.run("sphinx-build", "./docs", "./docs/_build")


@nox.session
def tests(session: nox.sessions.Session) -> None:
    """Run all tests."""
    args = session.posargs or ["-s"]
    session.run("poetry", "install", "--no-dev", external=True)
    install_with_constraints(session, "aresponses", "pytest", "pytest-aiohttp")
    session.run("pytest", *args)

# noxfile.py
"""
    Nox sessions.

    See `Cjolowicz's article <https://cjolowicz.github.io/posts/hypermodern-python-03-linting>`_
"""

import tempfile
from typing import Any

import nox
from nox.sessions import Session

nox.options.sessions = (
    "safety",
    "lint",
    "mypy",
    # "xdoctest",
    "tests",
    "codecov",
    "docs",
)

locations = "mckit", "tests", "noxfile.py", "docs/source/conf.py"

supported_pythons = "3.9 3.8 3.7".split()
# mypy, black and lint only work with python 3.7: dependencies requirement
# TODO dvp: check, when updates are available
mypy_pythons = "3.7"
black_pythons = "3.7"
lint_pythons = "3.7"


def install_with_constraints(session: Session, *args: str, **kwargs: Any) -> None:
    """Install packages constrained by Poetry's lock file."""
    with tempfile.NamedTemporaryFile() as requirements:
        session.run(
            "poetry",
            "export",
            "--dev",
            "--format=requirements.txt",
            f"--output={requirements.name}",
            external=True,
        )
        session.install(f"--constraint={requirements.name}", *args, **kwargs)


@nox.session(python=supported_pythons)
def tests(session: Session) -> None:
    """Run the test suite."""
    args = session.posargs or ["--cov", "-m", "not e2e"]
    session.run("poetry", "install", "--no-dev", external=True)
    install_with_constraints(session, "pytest", "pytest-cov", "pytest-mock", "coverage")
    session.run("pytest", *args)
    session.run("coverage", "report", "--show-missing", "--skip-covered")
    session.run("coverage", "html")


@nox.session(python=lint_pythons)
def lint(session: Session) -> None:
    """Lint using flake8."""
    args = session.posargs or locations
    install_with_constraints(
        session,
        "flake8",
        "flake8-annotations",
        "flake8-bandit",
        "flake8-black",
        "flake8-bugbear",
        "flake8-docstrings",
        "flake8-import-order",
        "darglint",
    )
    session.run("flake8", *args)


@nox.session(python=black_pythons)  # TODO dvp: this doesn't work with 3.8 so far
def black(session: Session) -> None:
    """Run black code formatter."""
    args = session.posargs or locations
    install_with_constraints(session, "black")
    session.run("black", *args)


@nox.session(python="3.8")
def safety(session: Session) -> None:
    """Scan dependencies for insecure packages."""
    with tempfile.NamedTemporaryFile() as requirements:
        session.run(
            "poetry",
            "export",
            "--dev",
            "--format=requirements.txt",
            "--without-hashes",
            f"--output={requirements.name}",
            external=True,
        )
        install_with_constraints(session, "safety")
        session.run("safety", "check", f"--file={requirements.name}", "--full-report")


#  This dangerous on ill complex project: may cause cyclic dependency
#  on partial imports ( from ... import).
#  Uncomment when proper imports or noorder directive is applied in sensitive files.
#  Always test after reorganizing ill projects.
#
@nox.session(python="3.9")
def organize_imports(session: Session) -> None:
    from glob import glob

    install_with_constraints(session, "reorder-python-imports")
    search_patterns = [
        "*.py",
        "mckit/*.py",
        "tests/*.py",
        "benchmarks/*.py",
        "profiles/*.py",
        "adhoc/*.py",
    ]
    files_to_process = sum(map(lambda p: glob(p, recursive=True), search_patterns), [])
    session.run(
        "python",
        "-m",
        "reorder_python_imports",
        "--py36-plus",
        "--diff-only",
        "--application-directories",
        "mckit:tests:benchmarks:profiles",
        *files_to_process,
        external=True,
    )


@nox.session(python=mypy_pythons)
def mypy(session: Session) -> None:
    """Type-check using mypy."""
    args = session.posargs or locations
    install_with_constraints(session, "mypy")
    session.run(
        "mypy",
        # "--config",
        # "mypy.ini",  # TODO dvp: compute path to ini-file from test environment: maybe search upward.
        *args,
    )


@nox.session(python=supported_pythons)
def xdoctest(session: Session) -> None:
    """Run examples with xdoctest."""
    args = session.posargs or ["mckit"]
    session.run("poetry", "install", "--no-dev", external=True)
    install_with_constraints(session, "xdoctest")
    session.run("python", "-m", "xdoctest", *args)


@nox.session(python="3.8")
def docs(session: Session) -> None:
    """Build the documentation."""
    session.run("poetry", "install", "--no-dev", external=True)
    install_with_constraints(
        session,
        "sphinx",
        "sphinx-autobuild",
        "numpydoc",
        "sphinxcontrib-htmlhelp",
        "sphinxcontrib-jsmath",
        "sphinxcontrib-napoleon",
        "sphinxcontrib-qthelp",
        "sphinx-autodoc-typehints",
        "sphinx_autorun",
        "sphinx-rtd-theme",
    )
    if session.interactive:
        session.run(
            "sphinx-autobuild",
            "--port=0",
            "--open-browser",
            "docs/source",
            "docs/_build/html",
        )
    else:
        session.run("sphinx-build", "docs/source", "docs/_build")


@nox.session(python="3.7")
def codecov(session: Session) -> None:
    """Upload coverage data."""
    session.run("poetry", "install", "--no-dev", external=True)
    install_with_constraints(
        session,
        "coverage[toml]",
        "pytest",
        "pytest-cov",
        "pytest-mock",
        "coverage",
        "codecov",
    )
    # install_with_constraints(session, "coverage[toml]", "codecov")
    session.run("coverage", "xml", "--fail-under=0")
    session.run("codecov", *session.posargs)

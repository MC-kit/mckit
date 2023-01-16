"""Build mckit.

The `build` method from this module is called by poetry build system
to set up proper options for actual builder.

The module builds and arrange C-dependency ``nlopt`` before own build.
"""
from typing import Any, Dict, List, Optional

# import distutils.log as log
import shutil

from pathlib import Path
from pprint import pprint

from building.build_nlopt import build_nlopt
from building.extension_geometry import GeometryExtension
from building.extension_utils import MACOS, WIN, get_library_dir
from setuptools import Extension
from setuptools.command.build_ext import build_ext
from setuptools.dist import Distribution

DIR = Path(__file__).parent


class BinaryDistribution(Distribution):
    def is_pure(self):
        return False


def get_nlopt_lib_name() -> str:
    """Compute library name: this depends on OS and python version."""
    if MACOS:
        return f"libnlopt.dylib"
    if WIN:
        return f"Release/nlopt.dll"
    return f"libnlopt.so"


class MCKitBuilder(build_ext):
    def __init__(self, dist: Distribution, **kwargs) -> None:
        build_ext.__init__(self, dist, **kwargs)

    def finalize_options(self):
        build_ext.finalize_options(self)
        # Late import to use numpy installed on isolated build
        import numpy as np

        library_dir = get_library_dir()
        self.library_dirs.append(str(library_dir))
        self.include_dirs.append(np.get_include())
        self.include_dirs.append(str(library_dir.parent / "include"))

    def build_extension(self, extension: Extension) -> None:
        # assert extension.name == "mckit.geometry"
        nlopt_build_dir = build_nlopt(clean=True)
        nlopt_lib = nlopt_build_dir / get_nlopt_lib_name()
        # log.info(f"---***  builder.build_lib: {self.build_lib}")
        # log.info(f"---***  builder.include_dirs: {self.include_dirs}")
        # log.info(f"---***  builder.library_dirs: {self.library_dirs}")
        # log.info(f"---***  nlopt lib path: {nlopt_lib}")
        ext_dir = Path(self.get_ext_fullpath(extension.name)).parent.absolute()
        # log.info(f"---***  copy nlopt lib to {ext_dir}")
        if ext_dir.exists():
            save_library(ext_dir, nlopt_lib)
        save_library(DIR / "mckit", nlopt_lib)
        # log.info("---*** Defined geometry extension:")
        # log.info(str(extension))
        # log.info("---***")
        build_ext.build_extension(self, extension)
        # log.info("---*** Search geometry:")
        # log.info(list(DIR.glob("**/*geometry*")))


def build(setup_kwargs: Dict[str, Any]) -> None:
    """Set specific distribution options.

    This function is called with setup.py generated by pip from pyproject.toml.
    """
    update_package_data(setup_kwargs)
    update_setup_requires(setup_kwargs)
    geometry_extension = GeometryExtension()
    setup_kwargs.update(
        {
            "ext_modules": [geometry_extension],
            "cmdclass": {"build_ext": MCKitBuilder},
            "distclass": BinaryDistribution,
            "long_description": Path("README.rst").read_text(encoding="utf8"),
            "src_root": str(Path(__file__).parent),
        }
    )
    save_setup_kwargs(setup_kwargs)


def update_setup_requires(setup_kwargs: Dict[str, Any]) -> None:
    """Fix for poetry issue: it doesn't install setup requirements."""
    setup_requires = setup_kwargs.get("setup_requires")  # type: Optional[List[str]]
    assert setup_requires is None, "Poetry has created setup_requires! Check the setup-generated.py"
    setup_requires = [
        "poetry-core>=1.0.7",
        "setuptools>=58.1",
        "wheel",
        # "cmake>=3.18.4",
        # "numpy>=1.13",
        # "mkl-devel",
    ]
    setup_kwargs["setup_requires"] = setup_requires
    save_generated_setup()


def update_package_data(setup_kwargs: Dict[str, Any]) -> None:
    """Fix for poetry issue: it doesn't provide correct specification from `[tool.poetry].input` field."""
    package_data = [
        "data/isotopes.dat",
        "nlopt.dll" if WIN else "libnlopt*",
    ]
    setup_kwargs["package_data"] = {"mckit": package_data}


def save_library(destination: Path, so: Path) -> None:
    if not so.exists():
        raise FileNotFoundError(f"Cannot find shared library {so}")
    shutil.copy(str(so), str(destination))


def save_setup_kwargs(setup_kwargs: Dict[str, Any]) -> None:
    """Save resulting setup_kwargs for examining."""
    kwargs_path = Path(__file__).parent / "poetry_setup_kwargs.txt"
    with kwargs_path.open(mode="w") as fid:
        pprint(setup_kwargs, fid, indent=4)


def save_generated_setup() -> None:
    """Save generated setup.py.

    Poetry ignores MANIFEST.in on command: ::

        poetry build -f sdist.

    So, 3rd-party code and build scripts are not included. Besides, output format is just default one.

    However, command: ::

        python setup-generated.py sdist --formats=gztar,xztar,zip

    uses MANIFEST.in and creates proper sdist archives.
    This is used in GitHub Action "Release" (see `.github/workflows/release.yml`).
    Besides, the setup-generated.py script can be used for debugging of setup process.

        Note: ::

        This file is regenerated on every build, so, there's no reason to store it in Git.
    """
    my_dir = Path(__file__).parent
    src = my_dir / "setup.py"
    dst = my_dir / "setup-generated.py"
    if src.exists():
        shutil.copy(str(src), str(dst))

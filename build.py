from typing import Any, Dict, List, Optional

import distutils.log as log
import platform
import shutil
import sys

from pathlib import Path
from pprint import pprint

from build_nlopt import build_nlopt
from extension_geometry import geometry_extension
from extension_utils import SYSTEM_WINDOWS
from setuptools import Extension
from setuptools.command.build_ext import build_ext
from setuptools.dist import Distribution

#
# TODO dvp: check
#      https://software.intel.com/content/www/us/en/develop/tools/oneapi/components/onemkl/link-line-advisor.html
#


class BinaryDistribution(Distribution):
    def is_pure(self):  # noqa
        return False


def get_shared_lib_name(name: str) -> str:
    """Compute library name: this depends on OS and python version"""
    sys_name = platform.system()
    if sys_name == "Linux":
        if sys.platform.startswith("darwin"):
            return f"lib{name}.dylib"
        return f"lib{name}.so.0"
    if sys_name == "Darwin":
        return f"lib{name}.dylib"
    if sys_name == "Windows":
        return f"Release/{name}.dll"
    raise EnvironmentError(f"Unsupported system {sys_name}")


class MCKitBuilder(build_ext):
    def __init__(self, dist: Distribution, **kwargs) -> None:
        build_ext.__init__(self, dist, **kwargs)

    def finalize_options(self):
        build_ext.finalize_options(self)
        # Late import to use numpy installed on isolated build
        import numpy as np

        root_prefix = Path(sys.prefix)
        if SYSTEM_WINDOWS:
            root_prefix = root_prefix / "Library"
        self.include_dirs.append(np.get_include())
        self.include_dirs.append(str(root_prefix / "include"))
        library_dir = root_prefix / "lib"
        # TODO dvp: for mkl-2021.2.0 (and later?) in Linux and Mac
        #           add symbolic links to libraries having '1' in names in the directory
        #           to make linker happy
        self.library_dirs.append(str(library_dir))

    def build_extension(self, extension: Extension) -> None:
        assert extension.name == "mckit.geometry"
        ext_dir = Path(self.get_ext_fullpath(extension.name)).parent.absolute()
        nlopt_build_dir = build_nlopt(clean=True)
        nlopt_lib = nlopt_build_dir / get_shared_lib_name("nlopt")
        log.info(f"---***  builder.build_lib: {self.build_lib}")
        log.info(f"---***  builder.include_dirs: {self.include_dirs}")
        log.info(f"---***  builder.library_dirs: {self.library_dirs}")
        log.info(f"---***  nlopt lib path: {nlopt_lib}")
        build_ext.build_extension(self, extension)
        log.info(f"---***  copy nlopt lib to {ext_dir}")
        save_nlopt_lib_to_source(ext_dir, nlopt_lib)


def build(setup_kwargs: Dict[str, Any]) -> None:
    """
    Set specific distribution options.

    This function is called with setup.py generated by pip from pyproject.toml.
    """
    update_package_data(setup_kwargs)
    update_setup_requires(setup_kwargs)
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
    """fix for poetry issue: it doesn't install setup requirements"""
    setup_requires = setup_kwargs.get("setup_requires")  # type: Optional[List[str]]
    assert (
        setup_requires is None
    ), "Poetry has created setup_requires! Check the setup-generated.py"
    setup_requires = [
        "poetry-core>=1.0.0",
        "setuptools>=43.0",
        "wheel",
        "cmake>=3.18.4",
        "numpy>=1.13",
        "mkl-devel",
    ]
    setup_kwargs["setup_requires"] = setup_requires
    save_generated_setup()


def update_package_data(setup_kwargs: Dict[str, Any]) -> None:
    """ fix for poetry issue: it doesn't provide correct specification from `[tool.poetry].input` field"""
    package_data = [
        "data/isotopes.dat",
        "nlopt.dll" if SYSTEM_WINDOWS else "libnlopt*",
    ]
    setup_kwargs["package_data"] = {"mckit": package_data}


def save_nlopt_lib_to_source(mckit_package_path: Path, so: Path) -> None:
    if not so.exists():
        raise FileNotFoundError(f"Cannot find shared library {so}")
    shutil.copy(str(so), str(mckit_package_path))


def save_setup_kwargs(setup_kwargs: Dict[str, Any]) -> None:
    """Save resulting setup_kwargs for examining"""
    kwargs_path = Path(__file__).parent / "poetry_setup_kwargs.txt"
    with kwargs_path.open(mode="w") as fid:
        pprint(setup_kwargs, fid, indent=4)


def save_generated_setup() -> None:
    """Save generated setup.py

    Poetry ignores MANIFEST.in on command: ::

        poetry build -f sdist.

    So, 3rd-party code and build scripts are not included. Besides, output format is just default one.

    However, command: ::

        python setup-generated.py sdist --formats=gztar,xztar,zip

    uses MANIFEST.in and creates proper sdist archives.
    This is used in Github Action "Release" (see .github/workflows/release.yml).
    Besides, the setup-generated.py script can be used for debugging of setup process.

        Note: ::

        This file is regenerated on every build, so, there's no reason to store it in Git.
    """
    my_dir = Path(__file__).parent
    src = my_dir / "setup.py"
    dst = my_dir / "setup-generated.py"
    if src.exists():
        shutil.copy(str(src), str(dst))

"""Code to build mckit geometry C-extension."""
from __future__ import annotations

from typing import Iterable

import sys
import sysconfig

from pathlib import Path

from building.extension_utils import MACOS, WIN, get_library_dir
from setuptools import Extension as _Extension

# Debugging
# Example: https://pythonextensionpatterns.readthedocs.io/en/latest/compiler_flags.html
_DEBUG = False
_DEBUG_LEVEL = 0
# _DEBUG = True
# _DEBUG_LEVEL = 2


# See MKL linking options for various versions of MKL and OS:
# https://software.intel.com/content/www/us/en/develop/tools/oneapi/components/onemkl/link-line-advisor.html
#
# Windows (oneMKL 2021, MS-C/C++,64bit, c-32bit, shared library, no cluster):
# mkl_intel_lp64_dll.lib mkl_tbb_thread_dll.lib mkl_core_dll.lib tbb.lib

if not WIN:

    def _make_full_names(lib_dir: Path, mkl_libs: Iterable[str]) -> list[str]:
        """Add library directory and extension to an MKL library name.

        According to the recommendation
        https://community.intel.com/t5/Intel-oneAPI-Math-Kernel-Library/pypi-package-for-mkl-2021-2-0-is-not-linkable-under-Linux-and/m-p/1275110?profile.language=ru
        on Linux MKL requires full path to the library.
        This method construct appropriate paths and searches the libraries.

        Args:
            lib_dir: directory, where to search libraries
            mkl_libs: list of library names to find

        Returns:
             The list of found libraries.

        Raises:
            EnvironmentError: if a library is not found.
        """
        # TODO dvp: implement logic for other possible suffixes in future MKL versions
        if MACOS:
            suffix = "2.dylib"
        else:
            if sys.platform != "linux":
                msg = f"Unknown platform {sys.platform}"
                raise OSError(msg)
            suffix = "so.2"

        lib_paths: list[Path] = [lib_dir / f"lib{_p}.{suffix}" for _p in mkl_libs]

        for p in lib_paths:
            if not p.exists():
                msg = f"{p} is not a valid path to an MKL library."
                raise OSError(msg)

        return [str(_p) for _p in lib_paths]


class GeometryExtension(_Extension):
    """The :class:`_Extension` specialization for mckit geometry module."""

    def __init__(self) -> None:
        super().__init__(
            "mckit.geometry",
            sources=list(map(str, Path("src", "mckit", "src").glob("*.c"))),
            language="c",
        )

        if WIN:
            cflags = ["/EHsc", "/bigobj"]
            ldflags = []
            libraries = [
                "mkl_rt",
                "nlopt",
            ]
        else:
            # Common flags for both release and debug builds.
            cflags = sysconfig.get_config_var("CFLAGS").split()
            cflags += ["-Wall", "-Wextra", "-m64"]
            if _DEBUG:
                cflags += ["-g3", "-O0", "-DDEBUG=%s" % _DEBUG_LEVEL, "-UNDEBUG"]
            else:
                cflags += ["-DNDEBUG", "-O3"]

            # env_cflags = os.environ.get("CFLAGS", "")
            # env_cppflags = os.environ.get("CPPFLAGS", "")
            # c_cpp_flags = shlex.split(env_cflags) + shlex.split(env_cppflags)
            # if not any(opt.startswith("-g") for opt in c_cpp_flags):
            #     cflags += ["-g0"]

            # Linker options (Linux 64bit, gcc, tbb):
            # https://www.intel.com/content/www/us/en/developer/tools/oneapi/onemkl-link-line-advisor.html#gs.rhcqqp
            # -L${MKLROOT}/lib/intel64 -Wl, --no-as-needed -lmkl_intel_ilp64 -lmkl_tbb_thread
            # -lmkl_core -lpthread -lm -ldl
            # Compiler options:
            # -DMKL_ILP64 -m64 -I"${MKLROOT}/include"
            lib_dir = get_library_dir(check=True)
            mkl_libs = ["mkl_rt"]
            # Intel recommended link arg "--no-as-needed", but is not available on macOS,
            # and doesn't affect other OS, let's omit it.
            ldflags = _make_full_names(lib_dir, mkl_libs)
            libraries = ["nlopt", "pthread", "m", "dl"]

        self._add_cflags(cflags)
        self._add_ldflags(ldflags)
        self._add_libraries(libraries)

    def _add_cflags(self, flags: list[str]) -> None:
        self.extra_compile_args[:0] = flags

    def _add_ldflags(self, flags: list[str]) -> None:
        self.extra_link_args[:0] = flags

    def _add_libraries(self, libraries: list[str]) -> None:
        self.libraries[:0] = libraries

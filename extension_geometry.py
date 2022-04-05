from typing import Iterable, List

import os
import shlex
import sys

from pathlib import Path

from extension_utils import MACOS, WIN, get_library_dir
from setuptools import Extension as _Extension

# See MKL linking options for various versions of MKL and OS:
# https://software.intel.com/content/www/us/en/develop/tools/oneapi/components/onemkl/link-line-advisor.html
#
# Windows (oneMKL 2021, MS-C/C++,64bit, c-32bit, shared library, no cluster):
# mkl_intel_lp64_dll.lib mkl_tbb_thread_dll.lib mkl_core_dll.lib tbb.lib

if not WIN:

    def _make_full_names(lib_dir: Path, mkl_libs: Iterable[str]) -> List[str]:
        """Add library directory and extension to an MKL library name.

        According to the recommendation
        https://community.intel.com/t5/Intel-oneAPI-Math-Kernel-Library/pypi-package-for-mkl-2021-2-0-is-not-linkable-under-Linux-and/m-p/1275110?profile.language=ru
        on Linux MKL requires full path to the library.
        """
        # TODO dvp: implement logic for other possible suffixes in future MKL versions
        if MACOS:
            suffix = "2.dylib"
        else:
            if sys.platform != "linux":
                raise EnvironmentError(f"Unknown platform {sys.platform}")
            suffix = "so.2"

        lib_paths = list(map(lambda _p: lib_dir / f"lib{_p}.{suffix}", mkl_libs))
        for p in lib_paths:
            if not p.exists():
                raise EnvironmentError(f"{p} is not a valid path to an MKL library.")
        return list(map(str, lib_paths))


class GeometryExtension(_Extension):
    def __init__(self) -> None:

        super().__init__(
            "mckit.geometry",
            sources=list(map(str, Path("mckit", "src").glob("*.c"))),
            language="c",
        )

        if WIN:
            # TODO dvp: check new Intel recommended options
            # define_macros = [("MKL_ILP64", None)]
            # mkl_intel_ilp64_dll.lib mkl_tbb_thread_dll.lib mkl_core_dll.lib tbb12.lib
            cflags = ["/EHsc", "/bigobj"]
            ldflags = []
            libraries = [
                "mkl_rt",
                "nlopt",
            ]
        else:
            cflags = [
                "-fvisibility=hidden",
                "-O3",
                "-Wall",
                "-m64",
            ]
            env_cflags = os.environ.get("CFLAGS", "")
            env_cppflags = os.environ.get("CPPFLAGS", "")
            c_cpp_flags = shlex.split(env_cflags) + shlex.split(env_cppflags)
            if not any(opt.startswith("-g") for opt in c_cpp_flags):
                cflags += ["-g0"]
            # Linker options (Linux 64bit, gcc, tbb):
            # https://www.intel.com/content/www/us/en/developer/tools/oneapi/onemkl-link-line-advisor.html#gs.rhcqqp
            # -L${MKLROOT}/lib/intel64 -Wl, --no-as-needed -lmkl_intel_ilp64 -lmkl_tbb_thread
            # -lmkl_core -lpthread -lm -ldl
            # Compiler options:
            # -DMKL_ILP64 -m64 -I"${MKLROOT}/include"
            lib_dir = get_library_dir(check=True)
            # mkl_libs = [
            #     "mkl_intel_ilp64",
            #     "mkl_tbb_thread",
            #     "mkl_core",
            # ]  # - this is recommended
            mkl_libs = ["mkl_rt"]  # - this actually works
            # TODO dvp: recommended "--no-as-needed" is not available on MacOS, decide if it is necessary
            # extra_link_args = ["-Wl,--no-as-needed"] + _make_full_names(lib_dir, mkl_libs)
            ldflags = _make_full_names(lib_dir, mkl_libs)
            libraries = ["nlopt", "pthread", "m", "dl"]

        self._add_cflags(cflags)
        self._add_ldflags(ldflags)
        self._add_libraries(libraries)

    def _add_cflags(self, flags: List[str]) -> None:
        self.extra_compile_args[:0] = flags

    def _add_ldflags(self, flags: List[str]) -> None:
        self.extra_link_args[:0] = flags

    def _add_libraries(self, libraries: List[str]) -> None:
        self.libraries[:0] = libraries

from __future__ import annotations

import shutil
from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py as _build_py


class build_py(_build_py):
    def run(self) -> None:
        static_build_dir = Path(self.build_lib) / "validex" / "static"
        source_static_dir = (Path(__file__).resolve().parent / "validex" / "static").resolve()
        resolved_static_build_dir = static_build_dir.resolve()
        if resolved_static_build_dir == source_static_dir:
            raise RuntimeError(
                f"Refusing to remove source package static directory: {static_build_dir}"
            )
        if static_build_dir.is_symlink():
            raise RuntimeError(
                f"Refusing to remove symlinked package static cache: {static_build_dir}"
            )
        if static_build_dir.exists():
            shutil.rmtree(static_build_dir)
        super().run()


setup(cmdclass={"build_py": build_py})

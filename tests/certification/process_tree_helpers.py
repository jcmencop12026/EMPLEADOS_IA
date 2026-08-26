"""Harness portable para pruebas adversariales de process tree (Windows/Linux)."""
from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass


@dataclass
class ProcessTreeHarness:
    script_path: str
    env: dict[str, str]
    parent_marker: str
    child_marker: str
    grand_marker: str | None = None

    def cleanup_script(self) -> None:
        try:
            os.unlink(self.script_path)
        except OSError:
            pass

    def cleanup_markers(self) -> None:
        for path in (self.parent_marker, self.child_marker, self.grand_marker):
            if path and os.path.exists(path):
                os.unlink(path)


def _marker_paths(suffix: str) -> tuple[str, str, str | None]:
    parent = tempfile.mktemp(suffix=f".{suffix}.parent.marker")
    child = tempfile.mktemp(suffix=f".{suffix}.child.marker")
    grand = tempfile.mktemp(suffix=f".{suffix}.grand.marker")
    for path in (parent, child, grand):
        if os.path.exists(path):
            os.unlink(path)
    return parent, child, grand


def build_parent_child_harness(suffix: str = "adv") -> ProcessTreeHarness:
    """Padre → hijo usando script temporal y variables de entorno (sin rutas en -c)."""
    parent_marker, child_marker, _ = _marker_paths(suffix)
    script_content = """import os, subprocess, sys, time
subprocess.Popen(
    [sys.executable, "-c", "import os,time; time.sleep(30); open(os.environ['M'],'w').write('c')"],
    env={**os.environ, "M": os.environ["PT_CHILD"]},
)
time.sleep(30)
open(os.environ["PT_PARENT"], "w").write("p")
"""
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as script_file:
        script_file.write(script_content)
        script_path = script_file.name
    env = {**os.environ, "PT_PARENT": parent_marker, "PT_CHILD": child_marker}
    return ProcessTreeHarness(
        script_path=script_path,
        env=env,
        parent_marker=parent_marker,
        child_marker=child_marker,
    )


def build_parent_child_grandchild_harness(suffix: str = "adv") -> ProcessTreeHarness:
    """Padre → hijo → nieto usando script temporal y variables de entorno."""
    parent_marker, child_marker, grand_marker = _marker_paths(suffix)
    script_content = """import os, subprocess, sys, time
subprocess.Popen(
    [sys.executable, "-c", "import os,time; time.sleep(30); open(os.environ['M'],'w').write('g')"],
    env={**os.environ, "M": os.environ["PT_GRAND"]},
)
subprocess.Popen(
    [sys.executable, "-c", "import os,time; time.sleep(30); open(os.environ['M'],'w').write('c')"],
    env={**os.environ, "M": os.environ["PT_CHILD"]},
)
time.sleep(30)
open(os.environ["PT_PARENT"], "w").write("p")
"""
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as script_file:
        script_file.write(script_content)
        script_path = script_file.name
    env = {
        **os.environ,
        "PT_PARENT": parent_marker,
        "PT_CHILD": child_marker,
        "PT_GRAND": grand_marker,
    }
    return ProcessTreeHarness(
        script_path=script_path,
        env=env,
        parent_marker=parent_marker,
        child_marker=child_marker,
        grand_marker=grand_marker,
    )

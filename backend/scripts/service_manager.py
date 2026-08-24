"""Gestión de servicios EMPLEADOS_IA con registro de PID propio (CURSOR-805C)."""
from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_DIR.parent


def pid_file_path(data_dir: Path | None = None) -> Path:
    base = data_dir or (PROJECT_ROOT / "data")
    return base / "empleados_ia.pids"


def resolve_npm() -> str:
    """Resuelve npm de forma portable (Windows: npm.cmd)."""
    if sys.platform == "win32":
        for candidate in ("npm.cmd", "npm.exe", "npm"):
            found = shutil.which(candidate)
            if found:
                return found
        raise RuntimeError("npm no encontrado en PATH")
    found = shutil.which("npm")
    if not found:
        raise RuntimeError("npm no encontrado en PATH")
    return found


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_proc_cmdline(pid: int) -> str:
    if sys.platform == "win32":
        try:
            out = subprocess.check_output(
                ["powershell", "-NoProfile", "-Command",
                 f"(Get-CimInstance Win32_Process -Filter \"ProcessId={pid}\").CommandLine"],
                text=True,
                stderr=subprocess.DEVNULL,
            )
            return out.strip()
        except Exception:
            return ""
    proc = Path(f"/proc/{pid}/cmdline")
    if proc.exists():
        return proc.read_text(errors="replace").replace("\x00", " ")
    return ""


def _read_proc_cwd(pid: int) -> str:
    if sys.platform == "win32":
        return ""
    proc_cwd = Path(f"/proc/{pid}/cwd")
    if proc_cwd.exists():
        try:
            return os.readlink(proc_cwd)
        except OSError:
            return ""
    return ""


def _is_empleados_ia_process(pid: int, role: str, entry: dict[str, Any] | None = None) -> bool:
    cmd = _read_proc_cmdline(pid).lower().replace("\\", "/")
    cwd = (_read_proc_cwd(pid) or (entry or {}).get("cwd", "")).lower().replace("\\", "/")
    project_hint = str(PROJECT_ROOT).replace("\\", "/").lower()
    if project_hint not in cwd and "empleados_ia" not in cwd and "empleados-ia" not in cwd:
        return False
    markers = {
        "backend": ["app.main:app", "uvicorn"],
        "frontend": ["vite", "empleados-ia-frontend", "npm"],
    }
    role_markers = markers.get(role, [])
    return any(m.lower() in cmd for m in role_markers)


def save_pid_registry(registry: dict[str, Any], data_dir: Path | None = None) -> Path:
    path = pid_file_path(data_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(registry, indent=2), encoding="utf-8")
    return path


def load_pid_registry(data_dir: Path | None = None) -> dict[str, Any]:
    path = pid_file_path(data_dir)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def stop_registered_services(data_dir: Path | None = None, dry_run: bool = False) -> dict[str, Any]:
    registry = load_pid_registry(data_dir)
    result: dict[str, Any] = {"stopped": [], "skipped": [], "errors": []}
    for role in ("backend", "frontend"):
        entry = registry.get(role)
        if not entry:
            continue
        pid = int(entry["pid"])
        if not _is_empleados_ia_process(pid, role, entry):
            result["skipped"].append({"role": role, "pid": pid, "reason": "no pertenece a EMPLEADOS_IA"})
            continue
        if dry_run:
            result["stopped"].append({"role": role, "pid": pid, "dry_run": True})
            continue
        try:
            os.kill(pid, signal.SIGTERM)
            result["stopped"].append({"role": role, "pid": pid})
        except ProcessLookupError:
            result["skipped"].append({"role": role, "pid": pid, "reason": "proceso no existe"})
        except Exception as exc:
            result["errors"].append({"role": role, "pid": pid, "error": str(exc)})

    if not dry_run:
        path = pid_file_path(data_dir)
        if path.exists():
            path.unlink()
    return result


def wait_for_health(url: str, timeout_sec: int = 30) -> bool:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status == 200:
                    return True
        except (urllib.error.URLError, TimeoutError):
            pass
        time.sleep(1)
    return False


def start_backend(port: int = 8010, database_url: str | None = None) -> dict[str, Any]:
    env = os.environ.copy()
    if database_url:
        env["DATABASE_URL"] = database_url
    log_path = PROJECT_ROOT / "data" / "backend.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_file = open(log_path, "a", encoding="utf-8")
    executable = sys.executable
    command = [executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", f"--port={port}"]
    proc = subprocess.Popen(
        command,
        cwd=str(BACKEND_DIR),
        env=env,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    return {
        "role": "backend",
        "pid": proc.pid,
        "port": port,
        "log": str(log_path),
        "cwd": str(BACKEND_DIR),
        "executable": executable,
        "command": " ".join(command),
        "started_at": _utcnow_iso(),
        "project_root": str(PROJECT_ROOT),
    }


def start_frontend(port: int = 5180) -> dict[str, Any]:
    log_path = PROJECT_ROOT / "data" / "frontend.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_file = open(log_path, "a", encoding="utf-8")
    npm = resolve_npm()
    command = [npm, "run", "dev", "--", "--host", "127.0.0.1", "--port", str(port)]
    proc = subprocess.Popen(
        command,
        cwd=str(PROJECT_ROOT / "frontend"),
        stdout=log_file,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    return {
        "role": "frontend",
        "pid": proc.pid,
        "port": port,
        "log": str(log_path),
        "cwd": str(PROJECT_ROOT / "frontend"),
        "executable": npm,
        "command": " ".join(command),
        "started_at": _utcnow_iso(),
        "project_root": str(PROJECT_ROOT),
    }

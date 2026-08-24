"""Gestión de servicios EMPLEADOS_IA con registro de PID y árbol de procesos (CURSOR-805D)."""
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


def _collect_descendant_pids(root_pid: int) -> list[int]:
    """Recoge PIDs descendientes del proceso raíz (npm.cmd → node/vite en Windows)."""
    descendants: list[int] = []
    if sys.platform == "win32":
        try:
            out = subprocess.check_output(
                [
                    "powershell", "-NoProfile", "-Command",
                    (
                        f"$root={root_pid}; "
                        "$all = Get-CimInstance Win32_Process; "
                        "$children = @{}; "
                        "foreach ($p in $all) { $pp = $p.ParentProcessId; "
                        "if (-not $children.ContainsKey($pp)) { $children[$pp] = @() }; "
                        "$children[$pp] += $p.ProcessId }; "
                        "$queue = [System.Collections.Generic.Queue[int]]::new(); "
                        "$queue.Enqueue($root); "
                        "$seen = @{}; "
                        "while ($queue.Count -gt 0) { "
                        "$pid = $queue.Dequeue(); "
                        "if ($seen.ContainsKey($pid)) { continue }; "
                        "$seen[$pid] = $true; "
                        "if ($pid -ne $root) { $descendants += $pid }; "
                        "if ($children.ContainsKey($pid)) { foreach ($c in $children[$pid]) { $queue.Enqueue($c) } } "
                        "}; "
                        "$descendants -join ','"
                    ),
                ],
                text=True,
                stderr=subprocess.DEVNULL,
            )
            if out.strip():
                descendants = [int(p) for p in out.strip().split(",") if p.strip().isdigit()]
        except Exception:
            descendants = []
    else:
        try:
            out = subprocess.check_output(
                ["ps", "-o", "pid=", "--ppid", str(root_pid)],
                text=True,
                stderr=subprocess.DEVNULL,
            )
            for line in out.splitlines():
                line = line.strip()
                if line.isdigit():
                    child = int(line)
                    descendants.append(child)
                    descendants.extend(_collect_descendant_pids(child))
        except Exception:
            pass
    return descendants


def _is_empleados_ia_process(pid: int, role: str, entry: dict[str, Any] | None = None) -> bool:
    cmd = _read_proc_cmdline(pid).lower().replace("\\", "/")
    cwd = (_read_proc_cwd(pid) or (entry or {}).get("cwd", "")).lower().replace("\\", "/")
    project_hint = str(PROJECT_ROOT).replace("\\", "/").lower()
    if project_hint not in cwd and "empleados_ia" not in cwd and "empleados-ia" not in cwd:
        if entry and entry.get("project_root"):
            pr = str(entry["project_root"]).replace("\\", "/").lower()
            if project_hint not in pr and "empleados_ia" not in pr:
                return False
        elif project_hint not in cwd:
            return False
    markers = {
        "backend": ["app.main:app", "uvicorn"],
        "frontend": ["vite", "empleados-ia-frontend", "npm"],
    }
    role_markers = markers.get(role, [])
    return any(m.lower() in cmd for m in role_markers)


def _terminate_pid(pid: int) -> None:
    if sys.platform == "win32":
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    else:
        try:
            os.killpg(os.getpgid(pid), signal.SIGTERM)
        except ProcessLookupError:
            pass
        except Exception:
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass


def _terminate_process_tree(entry: dict[str, Any]) -> list[int]:
    root_pid = int(entry["pid"])
    role = entry.get("role", "")
    if not _is_empleados_ia_process(root_pid, role, entry):
        return []

    stopped: list[int] = []
    child_pids = entry.get("child_pids") or _collect_descendant_pids(root_pid)
    for pid in reversed(child_pids):
        if _is_empleados_ia_process(pid, role, entry) or role == "frontend":
            _terminate_pid(pid)
            stopped.append(pid)

    _terminate_pid(root_pid)
    stopped.append(root_pid)
    return stopped


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
    for role in ("frontend", "backend"):
        entry = registry.get(role)
        if not entry:
            continue
        root_pid = int(entry["pid"])
        if not _is_empleados_ia_process(root_pid, role, entry):
            result["skipped"].append({"role": role, "pid": root_pid, "reason": "no pertenece a EMPLEADOS_IA"})
            continue
        if dry_run:
            result["stopped"].append({"role": role, "pid": root_pid, "dry_run": True})
            continue
        try:
            pids = _terminate_process_tree(entry)
            result["stopped"].append({"role": role, "root_pid": root_pid, "pids": pids})
        except Exception as exc:
            result["errors"].append({"role": role, "pid": root_pid, "error": str(exc)})

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
    time.sleep(0.5)
    child_pids = _collect_descendant_pids(proc.pid)
    return {
        "role": "backend",
        "pid": proc.pid,
        "child_pids": child_pids,
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
    time.sleep(1.0)
    child_pids = _collect_descendant_pids(proc.pid)
    return {
        "role": "frontend",
        "pid": proc.pid,
        "child_pids": child_pids,
        "port": port,
        "log": str(log_path),
        "cwd": str(PROJECT_ROOT / "frontend"),
        "executable": npm,
        "command": " ".join(command),
        "started_at": _utcnow_iso(),
        "project_root": str(PROJECT_ROOT),
    }

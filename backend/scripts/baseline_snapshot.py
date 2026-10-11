#!/usr/bin/env python3
"""Línea base verificable INFIJ/FÁBRICA-J — respaldo datado de BD, .env y manifiesto SHA-256."""
from __future__ import annotations

import hashlib
import json
import shutil
import tarfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
BASELINES = DATA / "BASELINES"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    dest = BASELINES / f"BASELINE_{stamp}"
    dest.mkdir(parents=True, exist_ok=True)

    manifest: dict = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "project_root": str(ROOT),
        "git_head": None,
        "files": [],
    }

    git_head = ROOT / ".git" / "HEAD"
    if git_head.is_file():
        manifest["git_head"] = git_head.read_text(encoding="utf-8").strip()

    candidates: list[Path] = []
    db = DATA / "enterprise_ai_os.db"
    if db.is_file():
        candidates.append(db)
    env_local = ROOT / ".env"
    if env_local.is_file():
        candidates.append(env_local)
    candidates.append(ROOT / "backend" / "app" / "config.py")

    archive_path = dest / f"snapshot_{stamp}.tar.gz"
    with tarfile.open(archive_path, "w:gz") as tar:
        for path in candidates:
            if not path.is_file():
                continue
            arcname = path.relative_to(ROOT).as_posix()
            tar.add(path, arcname=arcname)
            manifest["files"].append(
                {
                    "path": arcname,
                    "sha256": _sha256_file(path),
                    "size_bytes": path.stat().st_size,
                }
            )

    manifest_path = dest / "MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    verify_script = dest / "VERIFY.txt"
    verify_script.write_text(
        f"Restauración manual: extraer {archive_path.name} sobre {ROOT}\n"
        f"Comparar SHA-256 con MANIFEST.json antes de sobrescribir.\n",
        encoding="utf-8",
    )
    print(json.dumps({"baseline_dir": str(dest), "archive": str(archive_path), "files": len(manifest["files"])}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

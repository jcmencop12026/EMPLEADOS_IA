"""Agent B — C1 PostgreSQL data certification runner (isolated DB, no product changes)."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, urlunparse

ROOT = Path(__file__).resolve().parents[3]
BACKEND = ROOT / "backend"
ARTIFACTS = Path(__file__).resolve().parent
DUMP_PATH = ARTIFACTS / "c1_v1_pre_upgrade.dump"
RESULTS_PATH = ARTIFACTS / "cert_results.json"

V1_HEAD = "d1e2f3a4b5c6"
V2_HEAD = "1341a1b2c3d4e"
C1_SHA = "25ad1021ee6ea0322aceb0622252e7b748706d32"
DB_NAME = "empleados_ia_c1_b_cert"

NOW = datetime.now(timezone.utc).isoformat()


def pg_url(dbname: str | None = None) -> str:
    raw = os.environ.get("PG_TEST_URL") or os.environ.get("PG_URL") or os.environ.get("DATABASE_URL")
    if not raw:
        raise RuntimeError("No PG_TEST_URL / PG_URL / DATABASE_URL")
    u = raw.replace("postgresql+psycopg2", "postgresql", 1).replace("postgresql+asyncpg", "postgresql", 1)
    p = urlparse(u)
    if dbname:
        p = p._replace(path=f"/{dbname}")
    return urlunparse(p)


def run(cmd: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd or ROOT)
    if check and r.returncode != 0:
        print("COMMAND FAILED:", " ".join(cmd))
        print(r.stderr or r.stdout)
        sys.exit(1)
    return r


def psql(sql: str, db: str) -> str:
    r = run(["psql", pg_url(db), "-v", "ON_ERROR_STOP=1", "-t", "-A", "-c", sql])
    return r.stdout.strip()


def main() -> None:
    os.chdir(BACKEND)
    sys.path.insert(0, str(BACKEND))

    from app.security import hash_password  # noqa: WPS433

    results: dict = {
        "sha_c1": C1_SHA,
        "timestamp_utc": NOW,
        "db_name": DB_NAME,
        "v1_head": V1_HEAD,
        "v2_head_expected": V2_HEAD,
    }

    # PostgreSQL version
    pg_ver = run(["psql", "--version"]).stdout.strip()
    server_ver = psql("SHOW server_version;", "postgres")
    results["postgresql_client"] = pg_ver
    results["postgresql_server"] = server_ver

    admin = pg_url("postgres")
    run(["psql", admin, "-v", "ON_ERROR_STOP=1", "-c", f"DROP DATABASE IF EXISTS {DB_NAME};"])
    run(["psql", admin, "-v", "ON_ERROR_STOP=1", "-c", f"CREATE DATABASE {DB_NAME};"])

    os.environ["DATABASE_URL"] = pg_url(DB_NAME)

    # 1) Alembic to V1
    run([sys.executable, "-m", "alembic", "upgrade", V1_HEAD], cwd=BACKEND)
    alembic_init = psql("SELECT version_num FROM alembic_version;", DB_NAME)
    results["alembic_inicial"] = alembic_init
    if alembic_init != V1_HEAD:
        results["veredicto"] = "C1 DATOS NO APTO"
        results["error"] = f"alembic inicial {alembic_init} != {V1_HEAD}"
        RESULTS_PATH.write_text(json.dumps(results, indent=2), encoding="utf-8")
        sys.exit(1)

    pwd_hash = hash_password("C1CertB*Test2026")
    ts = "2026-08-31T12:00:00+00:00"

    seed_sql = f"""
    INSERT INTO organizations (id, name, created_at, status, timezone, slug, updated_at)
    VALUES
      ('c1a00001-0001-4001-8001-000000000001', 'Org C1 Cert A', '{ts}', 'ACTIVE', 'America/Bogota', 'org-c1-cert-a', '{ts}'),
      ('c1a00001-0001-4001-8001-000000000002', 'Org C1 Cert B', '{ts}', 'ACTIVE', 'America/Bogota', 'org-c1-cert-b', '{ts}');

    INSERT INTO users (id, organization_id, username, password_hash, role, is_active, created_at, status)
    VALUES
      ('c1u00001-0001-4001-8001-000000000001', 'c1a00001-0001-4001-8001-000000000001', 'admin_c1_a', '{pwd_hash}', 'superadmin', true, '{ts}', 'ACTIVE'),
      ('c1u00001-0001-4001-8001-000000000002', 'c1a00001-0001-4001-8001-000000000002', 'admin_c1_b', '{pwd_hash}', 'admin', true, '{ts}', 'ACTIVE');

    INSERT INTO ai_employees (
      id, organization_id, name, specialty, status, is_active, created_at,
      code, lifecycle_status, maturity, risk_level, version, shadow_mode, updated_at,
      created_by_id, owner_id
    ) VALUES
      ('c1e00001-0001-4001-8001-000000000001', 'c1a00001-0001-4001-8001-000000000001', 'Empleado A1', 'general', 'ACTIVE', true, '{ts}',
       'emp-a1', 'PUBLISHED', 'MATURE', 'LOW', 1, false, '{ts}',
       'c1u00001-0001-4001-8001-000000000001', 'c1u00001-0001-4001-8001-000000000001'),
      ('c1e00001-0001-4001-8001-000000000002', 'c1a00001-0001-4001-8001-000000000002', 'Empleado B1', 'general', 'ACTIVE', true, '{ts}',
       'emp-b1', 'PUBLISHED', 'MATURE', 'LOW', 1, false, '{ts}',
       'c1u00001-0001-4001-8001-000000000002', 'c1u00001-0001-4001-8001-000000000002');

    INSERT INTO employee_versions (id, employee_id, version, configuration_json, status, created_by_id, created_at)
    VALUES
      ('c1v00001-0001-4001-8001-000000000001', 'c1e00001-0001-4001-8001-000000000001', 1, '{{"seed":"c1"}}', 'PUBLISHED', 'c1u00001-0001-4001-8001-000000000001', '{ts}'),
      ('c1v00001-0001-4001-8001-000000000002', 'c1e00001-0001-4001-8001-000000000002', 1, '{{"seed":"c1"}}', 'PUBLISHED', 'c1u00001-0001-4001-8001-000000000002', '{ts}');
    """
    run(["psql", pg_url(DB_NAME), "-v", "ON_ERROR_STOP=1", "-c", seed_sql])

    pre_counts = {
        "organizations": int(psql("SELECT COUNT(*) FROM organizations;", DB_NAME)),
        "users": int(psql("SELECT COUNT(*) FROM users;", DB_NAME)),
        "ai_employees": int(psql("SELECT COUNT(*) FROM ai_employees;", DB_NAME)),
        "employee_versions": int(psql("SELECT COUNT(*) FROM employee_versions;", DB_NAME)),
    }
    results["pre_upgrade_counts"] = pre_counts

    # 2) Backup
    run(
        [
            "pg_dump",
            "-Fc",
            "-h",
            urlparse(pg_url(DB_NAME)).hostname or "localhost",
            "-p",
            str(urlparse(pg_url(DB_NAME)).port or 55432),
            "-U",
            urlparse(pg_url(DB_NAME)).username or "empleados",
            "-d",
            DB_NAME,
            "-f",
            str(DUMP_PATH),
        ],
        check=True,
    )
    dump_size = DUMP_PATH.stat().st_size
    sha256 = hashlib.sha256(DUMP_PATH.read_bytes()).hexdigest()
    list_out = run(["pg_restore", "--list", str(DUMP_PATH)]).stdout
    list_lines = [ln for ln in list_out.splitlines() if ln.strip()]
    backup_valid = len(list_lines) > 10 and dump_size > 0

    results["backup"] = {
        "real": True,
        "path": str(DUMP_PATH),
        "origen": f"isolated_db:{DB_NAME}@V1:{V1_HEAD}",
        "size_bytes": dump_size,
        "sha256": sha256,
        "pg_restore_list_lines": len(list_lines),
        "validado": backup_valid,
    }

    if not backup_valid:
        results["veredicto"] = "C1 DATOS NO APTO"
        results["error"] = "backup validation failed"
        RESULTS_PATH.write_text(json.dumps(results, indent=2), encoding="utf-8")
        sys.exit(1)

    # 3) Upgrade head
    run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=BACKEND)
    alembic_final = psql("SELECT version_num FROM alembic_version;", DB_NAME)
    results["alembic_final"] = alembic_final

    heads = run([sys.executable, "-m", "alembic", "heads"], cwd=BACKEND).stdout.strip()
    head_lines = [ln for ln in heads.splitlines() if "(head)" in ln]
    results["alembic_heads_raw"] = heads
    results["head_unico"] = len(head_lines) == 1 and V2_HEAD in heads

    # 4) bootstrap_permissions (idempotency x2)
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.seed_permissions import bootstrap_permissions

    engine = create_engine(os.environ["DATABASE_URL"])
    Session = sessionmaker(bind=engine)
    db = Session()
    bootstrap_permissions(db)
    perm_count_1 = int(psql("SELECT COUNT(*) FROM permissions;", DB_NAME))
    role_count_1 = int(psql("SELECT COUNT(*) FROM roles WHERE is_system = true;", DB_NAME))
    bootstrap_permissions(db)
    perm_count_2 = int(psql("SELECT COUNT(*) FROM permissions;", DB_NAME))
    role_count_2 = int(psql("SELECT COUNT(*) FROM roles WHERE is_system = true;", DB_NAME))
    db.close()
    engine.dispose()

    results["bootstrap_permissions"] = {
        "ejecutado": True,
        "permisos_tras_1": perm_count_1,
        "permisos_tras_2": perm_count_2,
        "roles_sistema_tras_1": role_count_1,
        "roles_sistema_tras_2": role_count_2,
        "idempotente": perm_count_1 == perm_count_2 and role_count_1 == role_count_2,
    }

    post_counts = {
        "organizations": int(psql("SELECT COUNT(*) FROM organizations;", DB_NAME)),
        "users": int(psql("SELECT COUNT(*) FROM users;", DB_NAME)),
        "ai_employees": int(psql("SELECT COUNT(*) FROM ai_employees;", DB_NAME)),
        "employee_versions": int(psql("SELECT COUNT(*) FROM employee_versions;", DB_NAME)),
        "permissions": int(psql("SELECT COUNT(*) FROM permissions;", DB_NAME)),
        "roles": int(psql("SELECT COUNT(*) FROM roles;", DB_NAME)),
    }
    results["post_upgrade_counts"] = post_counts

    no_data_loss = (
        post_counts["organizations"] >= pre_counts["organizations"]
        and post_counts["users"] >= pre_counts["users"]
        and post_counts["ai_employees"] >= pre_counts["ai_employees"]
        and post_counts["employee_versions"] >= pre_counts["employee_versions"]
    )
    results["integridad_sin_perdida"] = no_data_loss

    # 6b06 backfill
    ev_null_org = psql(
        "SELECT COUNT(*) FROM employee_versions WHERE organization_id IS NULL;",
        DB_NAME,
    )
    ev_total = psql("SELECT COUNT(*) FROM employee_versions;", DB_NAME)
    etc_null_org = psql(
        "SELECT COUNT(*) FROM employee_test_cases WHERE organization_id IS NULL;",
        DB_NAME,
    )
    has_last_training = psql(
        "SELECT COUNT(*) FROM information_schema.columns "
        "WHERE table_name='ai_employees' AND column_name='last_training_at';",
        DB_NAME,
    )
    results["backfill_6b06"] = {
        "employee_versions_null_org": int(ev_null_org),
        "employee_versions_total": int(ev_total),
        "employee_test_cases_null_org": int(etc_null_org),
        "ai_employees_has_last_training_at": int(has_last_training) == 1,
        "backfill_ok": int(ev_null_org) == 0 and int(ev_total) == pre_counts["employee_versions"],
    }

    # Multiempresa isolation sample
    cross_a = psql(
        "SELECT COUNT(*) FROM ai_employees WHERE organization_id = "
        "'c1a00001-0001-4001-8001-000000000001';",
        DB_NAME,
    )
    cross_b = psql(
        "SELECT COUNT(*) FROM ai_employees WHERE organization_id = "
        "'c1a00001-0001-4001-8001-000000000002';",
        DB_NAME,
    )
    results["multiempresa"] = {
        "org_a_employees": int(cross_a),
        "org_b_employees": int(cross_b),
        "aislado": int(cross_a) == 1 and int(cross_b) == 1,
    }

    # V2 structures sample
    v2_tables = [
        "employee_trainings",
        "employee_factory_approvals",
        "comm_channels",
        "gov_classification_levels",
    ]
    v2_present = {}
    for t in v2_tables:
        v2_present[t] = int(
            psql(
                f"SELECT COUNT(*) FROM information_schema.tables "
                f"WHERE table_schema='public' AND table_name='{t}';",
                DB_NAME,
            )
        ) == 1
    results["v2_structures_sample"] = v2_present

    # FK integrity sample
    fk_violations = psql(
        """
        SELECT COUNT(*) FROM ai_employees ae
        LEFT JOIN organizations o ON o.id = ae.organization_id
        WHERE o.id IS NULL;
        """,
        DB_NAME,
    )
    results["fk_ai_employees_org"] = int(fk_violations) == 0

    # validate_migrations
    vm = run([sys.executable, "scripts/validate_migrations.py"], cwd=BACKEND)
    results["validate_migrations"] = vm.returncode == 0

    apto = (
        alembic_init == V1_HEAD
        and alembic_final == V2_HEAD
        and results["head_unico"]
        and backup_valid
        and results["bootstrap_permissions"]["ejecutado"]
        and results["bootstrap_permissions"]["idempotente"]
        and no_data_loss
        and results["backfill_6b06"]["backfill_ok"]
        and results["multiempresa"]["aislado"]
        and results["fk_ai_employees_org"]
        and results["validate_migrations"]
    )

    results["postgresql_real"] = True
    results["veredicto"] = "C1 DATOS APTO" if apto else "C1 DATOS NO APTO"
    if not apto:
        results["fallos"] = [
            k
            for k, v in {
                "alembic_inicial": alembic_init == V1_HEAD,
                "alembic_final": alembic_final == V2_HEAD,
                "head_unico": results["head_unico"],
                "backup": backup_valid,
                "bootstrap": results["bootstrap_permissions"]["ejecutado"],
                "idempotente": results["bootstrap_permissions"]["idempotente"],
                "sin_perdida": no_data_loss,
                "backfill_6b06": results["backfill_6b06"]["backfill_ok"],
                "multiempresa": results["multiempresa"]["aislado"],
                "fk": results["fk_ai_employees_org"],
                "validate_migrations": results["validate_migrations"],
            }.items()
            if not v
        ]

    RESULTS_PATH.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))
    if not apto:
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env node
/** Orquestador certificación Macrobloque Integral V1 — PR #171 */
import { spawnSync } from "child_process";
import fs from "fs";
import path from "path";

const ARTIFACTS = process.env.EIAAX_ARTIFACTS || path.join(process.cwd(), "data", "evidence", "macrointegral-v1");
const SHA = process.env.EIAAX_SHA || "local";

function run(cmd, args, env = {}) {
  console.log(`\n>>> ${cmd} ${args.join(" ")}`);
  const r = spawnSync(cmd, args, { stdio: "inherit", env: { ...process.env, ...env }, shell: false });
  return r.status === 0;
}

async function main() {
  fs.mkdirSync(ARTIFACTS, { recursive: true });
  const results = [];

  results.push({ name: "frontend-build", pass: run("npm", ["run", "build"], { cwd: path.join(process.cwd(), "frontend") }) });

  results.push({
    name: "pytest-macrointegral",
    pass: run("python", ["-m", "pytest", "tests/test_macrointegral_v1_correcciones.py", "-v"], {
      PYTHONPATH: "backend:.",
    }),
  });

  const e2eScripts = [
    ["cert_transversal_visual.mjs", "transversal-visual"],
    ["cert_vista_empresa_flow.mjs", "vista-empresa-flow"],
  ];

  for (const [script, subdir] of e2eScripts) {
    const scriptPath = path.join(process.cwd(), "scripts", script);
    if (!fs.existsSync(scriptPath)) {
      results.push({ name: script, pass: false, skip: "script missing" });
      continue;
    }
    const ok = run("node", [scriptPath], {
      EIAAX_ARTIFACTS: path.join(ARTIFACTS, subdir),
      EIAAX_SHA: SHA,
    });
    results.push({ name: script, pass: ok });
  }

  const report = { sha: SHA, results, pass: results.every((r) => r.pass) };
  fs.writeFileSync(path.join(ARTIFACTS, "report.json"), JSON.stringify(report, null, 2));
  console.log("\n=== MACROINTEGRAL V1 ===");
  for (const r of results) console.log(r.pass ? "PASS" : "FAIL", r.name, r.skip ?? "");
  if (!report.pass) process.exit(1);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});

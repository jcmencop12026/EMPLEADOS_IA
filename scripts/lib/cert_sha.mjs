#!/usr/bin/env node
/** Coherencia SHA — certificaciones visuales deben corresponder al commit probado. */
import { execSync } from "child_process";
import fs from "fs";

export function gitHeadSha() {
  try {
    return execSync("git rev-parse HEAD", { encoding: "utf8" }).trim();
  } catch {
    return null;
  }
}

/**
 * Resuelve el SHA de certificación y falla si hay divergencia entre
 * git HEAD y EIAAX_CERT_SHA / EIAAX_SHA.
 * Nota: no usar process.env.GITHUB_SHA — en PRs GitHub Actions lo inyecta
 * con el merge commit sintético y no coincide con el checkout probado.
 */
export function resolveCertSha() {
  const head = gitHeadSha();
  const certSha = (process.env.EIAAX_CERT_SHA || process.env.EIAAX_SHA || "").trim();

  if (!head) {
    throw new Error("No se pudo obtener git rev-parse HEAD para certificación");
  }
  if (certSha && certSha !== head) {
    throw new Error(`EIAAX_CERT_SHA (${certSha}) ≠ git HEAD (${head})`);
  }

  return head;
}

export function assertReportSha(reportPath, expectedSha) {
  if (!fs.existsSync(reportPath)) {
    throw new Error(`report.json ausente: ${reportPath}`);
  }
  const report = JSON.parse(fs.readFileSync(reportPath, "utf8"));
  const reportSha = String(report.sha || "").trim();
  if (!reportSha) {
    throw new Error("report.json sin campo sha");
  }
  if (reportSha !== expectedSha) {
    throw new Error(`report.json sha (${reportSha}) ≠ esperado (${expectedSha})`);
  }
  return report;
}

export function writeShaManifest(artifactsDir, sha, extra = {}) {
  const manifest = {
    sha,
    git_head: gitHeadSha(),
    eiaax_cert_sha: process.env.EIAAX_CERT_SHA || process.env.EIAAX_SHA || null,
    github_actions_sha: process.env.GITHUB_SHA || null,
    generated_at: new Date().toISOString(),
    ...extra,
  };
  fs.writeFileSync(`${artifactsDir}/sha-manifest.json`, JSON.stringify(manifest, null, 2));
  return manifest;
}

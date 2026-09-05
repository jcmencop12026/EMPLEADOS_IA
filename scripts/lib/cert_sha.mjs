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
 * git HEAD, EIAAX_SHA y GITHUB_SHA.
 */
export function resolveCertSha() {
  const head = gitHeadSha();
  const envSha = (process.env.EIAAX_SHA || "").trim();
  const ghSha = (process.env.GITHUB_SHA || "").trim();
  const candidates = [head, envSha, ghSha].filter(Boolean);

  if (!head) {
    throw new Error("No se pudo obtener git rev-parse HEAD para certificación");
  }
  if (envSha && envSha !== head) {
    throw new Error(`EIAAX_SHA (${envSha}) ≠ git HEAD (${head})`);
  }
  if (ghSha && ghSha !== head) {
    throw new Error(`GITHUB_SHA (${ghSha}) ≠ git HEAD (${head})`);
  }
  if (envSha && ghSha && envSha !== ghSha) {
    throw new Error(`EIAAX_SHA (${envSha}) ≠ GITHUB_SHA (${ghSha})`);
  }

  const unique = [...new Set(candidates)];
  if (unique.length > 1) {
    throw new Error(`SHA incoherentes: ${unique.join(", ")}`);
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
    eiaax_sha: process.env.EIAAX_SHA || null,
    github_sha: process.env.GITHUB_SHA || null,
    generated_at: new Date().toISOString(),
    ...extra,
  };
  fs.writeFileSync(`${artifactsDir}/sha-manifest.json`, JSON.stringify(manifest, null, 2));
  return manifest;
}

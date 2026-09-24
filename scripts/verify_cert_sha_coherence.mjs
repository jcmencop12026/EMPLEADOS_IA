#!/usr/bin/env node
/** Verifica coherencia SHA entre git HEAD, report.json, manifests y nombre de artefacto CI. */
import fs from "fs";
import path from "path";
import { assertReportSha, resolveCertSha } from "./lib/cert_sha.mjs";

const root = process.cwd();
const certSha = resolveCertSha();
const artifactName = (process.env.EIAAX_ARTIFACT_NAME || "").trim();
const expectedArtifact = `eiaax-visual-pr171-${certSha}`;

const suites = [
  { dir: "data/evidence/transversal-visual", report: "report.json" },
  { dir: "data/evidence/vista-empresa-flow", report: "report.json" },
];

let ok = true;
for (const suite of suites) {
  const dir = path.join(root, suite.dir);
  const rp = path.join(dir, suite.report);
  try {
    const report = assertReportSha(rp, certSha);
    console.log("PASS", rp, "sha=", report.sha);
    const manifestPath = path.join(dir, "sha-manifest.json");
    if (!fs.existsSync(manifestPath)) {
      throw new Error(`sha-manifest.json ausente en ${suite.dir}`);
    }
    const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
    if (manifest.sha !== certSha) {
      throw new Error(`sha-manifest sha (${manifest.sha}) ≠ esperado (${certSha})`);
    }
    console.log("PASS", manifestPath);
  } catch (e) {
    ok = false;
    console.error("FAIL", rp, e.message);
  }
}

if (artifactName && artifactName !== expectedArtifact) {
  ok = false;
  console.error(`FAIL artefacto: ${artifactName} ≠ ${expectedArtifact}`);
} else if (artifactName) {
  console.log("PASS artefacto:", artifactName);
}

if (!ok) process.exit(1);
console.log("SHA coherence OK:", certSha);

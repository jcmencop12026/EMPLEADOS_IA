#!/usr/bin/env node
/** E2E flujo Vista Empresa — conserva expediente y contexto */
import { chromium } from "playwright";
import fs from "fs";
import path from "path";
import { assertReportSha, resolveCertSha, writeShaManifest } from "./lib/cert_sha.mjs";

const BASE = process.env.EIAAX_BASE || "http://127.0.0.1:5180";
const USER = process.env.EIAAX_USER || "org_a_admin";
const PASS = process.env.EIAAX_PASS || "DemoA2026!";
const ARTIFACTS = process.env.EIAAX_ARTIFACTS || path.join(process.cwd(), "data", "evidence", "vista-empresa-flow");

async function login(page) {
  await page.goto(`${BASE}/login`, { waitUntil: "domcontentloaded" });
  await page.fill('input[autocomplete="username"]', USER);
  await page.fill('input[type="password"]', PASS);
  await page.click("button.login-submit");
  await page.waitForFunction(() => !window.location.pathname.includes("/login"), { timeout: 20000 });
}

async function main() {
  const certSha = resolveCertSha();
  fs.mkdirSync(ARTIFACTS, { recursive: true });
  writeShaManifest(ARTIFACTS, certSha, { suite: "vista-empresa-flow" });

  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1366, height: 768 } });
  const defects = [];

  await login(page);
  const expId = await page.evaluate(async () => {
    const token = localStorage.getItem("eaios_token");
    const r = await fetch("/api/evaluaciones", { headers: { Authorization: `Bearer ${token}` } });
    const data = await r.json();
    const items = data.items || data;
    const h = items.find((e) => (e.entidad_nombre || "").includes("Horizonte"));
    return h?.id || items[0]?.id;
  });
  if (!expId) throw new Error("Sin expediente");

  // Cabina → Vista Empresa
  await page.goto(`${BASE}/evaluaciones/${expId}?tab=vista-empresa`, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(800);
  const url1 = page.url();
  if (!url1.includes(`evaluaciones/${expId}`)) defects.push("perdió expediente en cabina vista-empresa");
  if (!url1.includes("tab=vista-empresa")) defects.push("tab vista-empresa incorrecto");
  await page.screenshot({ path: path.join(ARTIFACTS, "01-vista-empresa-tab.png") });

  const body = await page.locator("body").innerText();
  if (/Crear entidad empresa/i.test(body)) defects.push("muestra crear entidad dentro de empresa existente");

  // Informes → publicable cliente (API backend)
  const apiCheck = await page.evaluate(async (id) => {
    const token = localStorage.getItem("eaios_token");
    const r = await fetch(`/api/evaluaciones/${id}/informe-publicable-cliente`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!r.ok) return { ok: false, status: r.status };
    const data = await r.json();
    const raw = JSON.stringify(data).toLowerCase();
    const forbidden = ["prompt", "margen", "finops", "scoring", "costo_interno"].some((k) => raw.includes(k));
    return { ok: data.audiencia === "PUBLICABLE_CLIENTE" && !forbidden, audiencia: data.audiencia };
  }, expId);
  if (!apiCheck.ok) defects.push("informe-publicable-cliente no válido");

  // Reload persiste contexto
  await page.reload({ waitUntil: "domcontentloaded" });
  await page.waitForTimeout(500);
  if (!page.url().includes("tab=vista-empresa")) defects.push("reload no conserva tab");
  if (!page.url().includes(expId)) defects.push("reload perdió expediente");

  // Regreso CC empresa (no Todas)
  await page.goto(`${BASE}/?expediente=${expId}`, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(500);
  if (!page.url().includes(`expediente=${expId}`)) defects.push("CC empresa perdió contexto");
  const ccBody = await page.locator("body").innerText();
  if (/Todas las empresas/i.test(ccBody) && !page.url().includes(`expediente=${expId}`)) {
    defects.push("volvió a Todas las empresas sin acción deliberada");
  }

  // Volver a cabina mismo expediente
  await page.goto(`${BASE}/evaluaciones/${expId}?tab=vista-empresa`, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(400);
  if (!page.url().includes(expId)) defects.push("regreso cabina perdió expediente");

  const report = {
    sha: certSha,
    git_head: certSha,
    github_sha: process.env.GITHUB_SHA || null,
    eiaax_sha: process.env.EIAAX_SHA || null,
    expId,
    defects,
    pass: defects.length === 0,
  };
  fs.writeFileSync(path.join(ARTIFACTS, "report.json"), JSON.stringify(report, null, 2));
  assertReportSha(path.join(ARTIFACTS, "report.json"), certSha);

  await browser.close();
  console.log(defects.length ? "FAIL" : "PASS", "Vista Empresa flow", defects.join("; ") || "", `sha=${certSha}`);
  if (defects.length) process.exit(1);
}

main().catch((e) => { console.error(e); process.exit(1); });

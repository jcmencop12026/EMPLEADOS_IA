#!/usr/bin/env node
/**
 * Certificación integración PR170 — navegación CC y persistencia ?tab=
 */
import { chromium } from "playwright";
import fs from "fs";
import path from "path";

const BASE = process.env.EIAAX_BASE || "http://127.0.0.1:5180";
const USER = process.env.EIAAX_USER || "org_a_admin";
const PASS = process.env.EIAAX_PASS || "DemoA2026!";
const ARTIFACTS = process.env.EIAAX_ARTIFACTS || path.join(process.cwd(), "data", "evidence", "integracion-pr170");

async function login(page) {
  await page.goto(`${BASE}/login`, { waitUntil: "domcontentloaded" });
  await page.fill('input[autocomplete="username"]', USER);
  await page.fill('input[type="password"]', PASS);
  await page.click("button.login-submit");
  await page.waitForFunction(() => !window.location.pathname.includes("/login"), { timeout: 20000 });
}

async function resolveHorizonteId(page) {
  const res = await page.evaluate(async () => {
    const token = localStorage.getItem("eaios_token");
    const r = await fetch("/api/evaluaciones", { headers: { Authorization: `Bearer ${token}` } });
    const data = await r.json();
    const items = data.items || data;
    const h = items.find((e) => (e.entidad_nombre || "").includes("Horizonte"));
    return h?.id || items[0]?.id;
  });
  return res;
}

async function main() {
  fs.mkdirSync(ARTIFACTS, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  const results = [];

  await login(page);
  const expId = await resolveHorizonteId(page);
  if (!expId) throw new Error("Sin expediente Horizonte");

  // A. CC → Siguiente acción → cabina con ?tab=
  await page.goto(`${BASE}/?expediente=${expId}`, { waitUntil: "domcontentloaded" });
  await page.waitForSelector(".siguiente-accion-panel", { timeout: 15000 });
  const irBtn = page.locator(".siguiente-accion-principal button.btn.primary").first();
  const hasBtn = await irBtn.count();
  let navOk = false;
  if (hasBtn) {
    await irBtn.click();
    await page.waitForTimeout(800);
    const url = page.url();
    navOk = url.includes(`/evaluaciones/${expId}`) && url.includes("tab=");
  }
  results.push({ name: "CC siguiente acción navega expediente+tab", pass: navOk });
  await page.screenshot({ path: path.join(ARTIFACTS, "01-cc-siguiente-accion.png") });

  // B. Persistencia ?tab=valor tras recarga
  await page.goto(`${BASE}/evaluaciones/${expId}?tab=valor`, { waitUntil: "domcontentloaded" });
  await page.waitForSelector(".tab-nav .active", { timeout: 15000 });
  const tabBefore = await page.locator(".tab-nav .active").innerText();
  await page.reload({ waitUntil: "domcontentloaded" });
  await page.waitForSelector(".tab-nav .active", { timeout: 15000 });
  const tabAfter = await page.locator(".tab-nav .active").innerText();
  const persistOk = /valor/i.test(tabBefore) && /valor/i.test(tabAfter);
  results.push({ name: "Persistencia ?tab=valor tras recarga", pass: persistOk });
  await page.screenshot({ path: path.join(ARTIFACTS, "02-tab-valor-reload.png") });

  await browser.close();

  const pass = results.filter((r) => r.pass).length;
  const fail = results.filter((r) => !r.pass).length;
  const report = { sha: process.env.EIAAX_SHA || "local", base: BASE, results, pass, fail };
  fs.writeFileSync(path.join(ARTIFACTS, "report.json"), JSON.stringify(report, null, 2));

  console.log("\n=== CERT INTEGRACION PR170 ===\n");
  for (const r of results) console.log(r.pass ? "PASS" : "FAIL", r.name);
  console.log(`\nPASS: ${pass} | FAIL: ${fail}`);
  if (fail > 0) process.exit(1);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});

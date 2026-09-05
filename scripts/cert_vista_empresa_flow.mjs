#!/usr/bin/env node
/** E2E flujo Vista Empresa — conserva expediente y contexto */
import { chromium } from "playwright";
import fs from "fs";
import path from "path";

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
  fs.mkdirSync(ARTIFACTS, { recursive: true });
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

  await page.goto(`${BASE}/evaluaciones/${expId}?tab=vista-empresa`, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(800);
  const url1 = page.url();
  if (!url1.includes(`evaluaciones/${expId}`)) defects.push("perdió expediente en cabina vista-empresa");
  if (!url1.includes("tab=vista-empresa")) defects.push("tab vista-empresa incorrecto");
  await page.screenshot({ path: path.join(ARTIFACTS, "01-vista-empresa-tab.png") });

  const body = await page.locator("body").innerText();
  if (/Crear entidad empresa/i.test(body)) defects.push("muestra crear entidad dentro de empresa existente");

  await page.reload({ waitUntil: "domcontentloaded" });
  await page.waitForTimeout(500);
  if (!page.url().includes(`tab=vista-empresa`)) defects.push("reload no conserva tab");
  if (!page.url().includes(expId)) defects.push("reload perdió expediente");

  await page.goto(`${BASE}/?expediente=${expId}`, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(500);
  if (!page.url().includes(`expediente=${expId}`)) defects.push("CC empresa perdió contexto");

  const report = { expId, defects, pass: defects.length === 0 };
  fs.writeFileSync(path.join(ARTIFACTS, "report.json"), JSON.stringify(report, null, 2));
  await browser.close();
  console.log(defects.length ? "FAIL" : "PASS", "Vista Empresa flow", defects.join("; ") || "");
  if (defects.length) process.exit(1);
}

main().catch((e) => { console.error(e); process.exit(1); });

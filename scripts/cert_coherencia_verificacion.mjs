#!/usr/bin/env node
/**
 * Verificación coherencia — capturas informes 4v, tablero, vista empresa, operaciones.
 */
import { chromium } from "playwright";
import fs from "fs";
import path from "path";

const BASE = process.env.EIAAX_BASE || "http://127.0.0.1:5180";
const USER = process.env.EIAAX_USER || "org_a_admin";
const PASS = process.env.EIAAX_PASS || "DemoA2026!";
const ARTIFACTS = process.env.EIAAX_ARTIFACTS || path.join(process.cwd(), "data", "evidence", "coherencia-verificacion");

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
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await login(page);

  const expId = await page.evaluate(async () => {
    const token = localStorage.getItem("eaios_token");
    const res = await fetch("/api/evaluaciones", { headers: { Authorization: `Bearer ${token}` } });
    const data = await res.json();
    return (data.items ?? []).find((i) => String(i.entidad_nombre ?? "").includes("Horizonte"))?.id ?? null;
  });
  if (!expId) throw new Error("Horizonte no encontrado");

  await page.goto(`${BASE}/?expediente=${expId}`, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(1200);
  await page.screenshot({ path: path.join(ARTIFACTS, "01-cc-horizonte-tablero.png"), fullPage: false });

  const informeTabs = ["Ejecutiva", "Operativa", "Resultados / Valor", "Publicable cliente"];
  for (let i = 0; i < informeTabs.length; i++) {
    await page.goto(`${BASE}/evaluaciones/${expId}`, { waitUntil: "domcontentloaded" });
    await page.getByRole("button", { name: /Informes/i }).first().click();
    await page.waitForTimeout(600);
    const btn = page.getByRole("button", { name: new RegExp(informeTabs[i].split("/")[0].trim(), "i") }).first();
    if (await btn.count()) await btn.click();
    await page.waitForTimeout(500);
    await page.screenshot({ path: path.join(ARTIFACTS, `02-informe-${i + 1}-${informeTabs[i].replace(/\s+/g, "-").toLowerCase()}.png`) });
  }

  await page.goto(`${BASE}/evaluaciones/${expId}?tab=vista-empresa`, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(800);
  await page.screenshot({ path: path.join(ARTIFACTS, "03-vista-empresa.png") });

  await page.goto(`${BASE}/operaciones`, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(800);
  const opsScroll = await page.evaluate(() => {
    const wrap = document.querySelector(".ops-table-panel");
    if (!wrap) return { ok: false, reason: "sin panel" };
    const actionsVisible = !!document.querySelector(".ops-hub-table td:last-child");
    return {
      ok: true,
      scrollable: wrap.scrollWidth > wrap.clientWidth,
      actionsVisible,
      clientWidth: wrap.clientWidth,
      scrollWidth: wrap.scrollWidth,
    };
  });
  await page.screenshot({ path: path.join(ARTIFACTS, "04-operaciones-tabla.png"), fullPage: false });

  await page.goto(`${BASE}/admin/configuracion`, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(600);
  await page.screenshot({ path: path.join(ARTIFACTS, "05-config-logo.png") });

  const report = { expId, opsScroll, artifacts: ARTIFACTS };
  fs.writeFileSync(path.join(ARTIFACTS, "report.json"), JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report, null, 2));
  await browser.close();
}

main().catch((e) => { console.error(e); process.exit(2); });

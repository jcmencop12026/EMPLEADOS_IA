#!/usr/bin/env node
/**
 * Inventario opciones visibles durante E2E V1 + estado tablas en recorrido.
 */
import { chromium } from "playwright";
import fs from "fs";
import path from "path";

const BASE = process.env.EIAAX_BASE || "http://127.0.0.1:5180";
const USER = process.env.EIAAX_USER || "org_a_admin";
const PASS = process.env.EIAAX_PASS || "DemoA2026!";
const ARTIFACTS = process.env.EIAAX_ARTIFACTS || path.join(process.cwd(), "data", "evidence", "opciones-e2e");

const RUTAS = [
  { path: "/", label: "Centro de Control", estado: "FUNCIONAL" },
  { path: "/empresas", label: "Empresas", estado: "FUNCIONAL" },
  { path: "/evaluaciones", label: "Evaluaciones", estado: "FUNCIONAL" },
  { path: "/operaciones", label: "Operaciones", estado: "FUNCIONAL" },
  { path: "/directorio", label: "Empleados IA", estado: "FUNCIONAL" },
  { path: "/oportunidades", label: "Oportunidades", estado: "FUNCIONAL" },
  { path: "/resultados-inteligencia", label: "Resultados", estado: "FUNCIONAL" },
  { path: "/comunicaciones", label: "Comunicaciones", estado: "FUNCIONAL" },
  { path: "/automatizaciones", label: "Automatizaciones", estado: "DEMO" },
  { path: "/ejecuciones", label: "Ejecuciones", estado: "FUNCIONAL" },
  { path: "/aprobaciones", label: "Aprobaciones", estado: "FUNCIONAL" },
  { path: "/ayuda/guia", label: "Instructivo", estado: "FUNCIONAL" },
  { path: "/demo", label: "Demo comercial", estado: "DEMO" },
];

async function login(page) {
  await page.goto(`${BASE}/login`, { waitUntil: "domcontentloaded" });
  await page.fill('input[autocomplete="username"]', USER);
  await page.fill('input[type="password"]', PASS);
  await page.click("button.login-submit");
  await page.waitForFunction(() => !window.location.pathname.includes("/login"), { timeout: 20000 });
}

async function auditTables(page, label = "") {
  const tables = page.locator("table.data-table, table.eiaax-table, table");
  const count = await tables.count();
  const issues = [];
  for (let i = 0; i < Math.min(count, 12); i++) {
    const t = tables.nth(i);
    const visible = await t.isVisible().catch(() => false);
    if (!visible) continue;
    const box = await t.boundingBox();
    if (box && box.width > 1400) issues.push(`${label}tabla ${i + 1} ancho ${Math.round(box.width)}`);
    const overflow = await t.evaluate((el) => {
      const wrap = el.closest(".table-wrap, .ops-table-panel, .panel, .ops-page") || el.parentElement;
      if (!wrap) return false;
      const isOpsIntentional = wrap.classList.contains("ops-table-panel") || el.classList.contains("ops-hub-table");
      if (isOpsIntentional) return false;
      return wrap.scrollWidth > wrap.clientWidth + 4;
    });
    if (overflow) issues.push(`${label}tabla ${i + 1} overflow horizontal`);
    const truncated = await t.evaluate((el) =>
      Array.from(el.querySelectorAll("td, th")).some((c) => c.scrollWidth > c.clientWidth + 2)
    );
    if (truncated) issues.push(`${label}tabla ${i + 1} texto cortado`);
  }
  return issues;
}

async function auditHorizonteCabina(page) {
  const token = await page.evaluate(() => localStorage.getItem("eaios_token"));
  const expId = await page.evaluate(async (t) => {
    const res = await fetch("/api/evaluaciones", { headers: { Authorization: `Bearer ${t}` } });
    const data = await res.json();
    const h = (data.items ?? []).find((i) => String(i.entidad_nombre ?? "").includes("Horizonte"));
    return h?.id ?? null;
  }, token);
  if (!expId) return [{ opcion: "Cabina Horizonte", ruta: "/evaluaciones", estado: "ROTA", defects: ["expediente Horizonte no encontrado"] }];

  const tabs = [
    { tab: "Empresa", label: "Cabina Empresa" },
    { tab: "Diagnóstico", label: "Cabina Diagnóstico" },
    { tab: "Valor", label: "Cabina Valor" },
    { tab: "Resultados", label: "Cabina Resultados" },
    { tab: "Informes", label: "Cabina Informes" },
    { tab: "Operaciones", label: "Cabina Operaciones" },
  ];
  const out = [];
  for (const { tab, label } of tabs) {
    await page.goto(`${BASE}/evaluaciones/${expId}`, { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(600);
    const tabBtn = page.getByRole("button", { name: new RegExp(tab, "i") }).first();
    if (await tabBtn.count()) {
      await tabBtn.click();
      await page.waitForTimeout(500);
    }
    const tableIssues = await auditTables(page, `${label}: `);
    out.push({
      opcion: label,
      ruta: `/evaluaciones/${expId}#${tab.toLowerCase()}`,
      estado: tableIssues.length ? "ROTA" : "FUNCIONAL",
      tabla_issues: tableIssues,
      defects: tableIssues,
    });
  }
  return out;
}

async function main() {
  fs.mkdirSync(ARTIFACTS, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e.message)));

  await login(page);
  const inventario = [];

  for (const ruta of RUTAS) {
    errors.length = 0;
    await page.goto(`${BASE}${ruta.path}`, { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(500);
    const body = await page.locator("body").innerText();
    const blank = body.trim().length < 30;
    const hard = errors.some((e) => /ReferenceError|Rules of Hooks/i.test(e));
    const tableIssues = await auditTables(page);
    let estado = ruta.estado;
    if (blank || hard) estado = "ROTA";
    inventario.push({
      opcion: ruta.label,
      ruta: ruta.path,
      estado,
      tabla_issues: tableIssues,
      defects: [...(blank ? ["pantalla blanca"] : []), ...(hard ? ["pageerror"] : []), ...tableIssues],
    });
  }

  inventario.push(...(await auditHorizonteCabina(page)));

  await browser.close();
  const report = {
    generated_at: new Date().toISOString(),
    inventario,
    rotas: inventario.filter((i) => i.estado === "ROTA").length,
    duplicadas: 0,
  };
  fs.writeFileSync(path.join(ARTIFACTS, "inventario.json"), JSON.stringify(report, null, 2));

  console.log("\n=== INVENTARIO OPCIONES E2E ===\n");
  for (const i of inventario) {
    console.log(`${i.estado.padEnd(12)} ${i.opcion} (${i.ruta}) ${i.defects.join("; ") || "—"}`);
  }
  console.log(`\nROTA=${report.rotas} | Report: ${path.join(ARTIFACTS, "inventario.json")}`);
  process.exit(report.rotas ? 1 : 0);
}

main().catch((e) => { console.error(e); process.exit(2); });

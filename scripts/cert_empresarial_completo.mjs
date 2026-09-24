#!/usr/bin/env node
/**
 * E2E empresarial completo — recorrido macrobloque revisión integral.
 */
import { chromium } from "playwright";
import fs from "fs";
import path from "path";

const BASE = process.env.EIAAX_BASE || "http://127.0.0.1:5180";
const USER = process.env.EIAAX_USER || "org_a_admin";
const PASS = process.env.EIAAX_PASS || "DemoA2026!";
const ARTIFACTS = process.env.EIAAX_ARTIFACTS || path.join(process.cwd(), "data", "evidence", "empresarial-e2e");

const STEPS = [
  { name: "01 Login", path: "/login", expect: /Iniciar sesión/i, layout: false },
  { name: "02 CC portafolio", path: "/", expect: /Centro de Control|Situación operativa/i },
  { name: "03 Horizonte contexto", path: null, expect: /Horizonte|Puesto de mando|Tablero empresarial/i },
  { name: "04 Conocer", path: null, expect: /Empresa|Información|Horizonte/i },
  { name: "05 Documentos", path: null, expect: /Información|Evidencias|documento/i },
  { name: "06 Evaluar", path: null, expect: /Evaluación|confianza|información/i },
  { name: "07 Diagnóstico", path: null, expect: /Diagnóstico|hallazgo|Cadena/i },
  { name: "08 Cadena analítica", path: null, expect: /Evidencia|Hallazgo|Oportunidad|Recomendación/i },
  { name: "09 Oportunidades", path: "/oportunidades", expect: /Oportunidad/i },
  { name: "10 Valorar", path: null, expect: /Valor|Verificado|Estimado|Potencial/i },
  { name: "11 Resultados indicadores", path: null, expect: /Antes|Proyectado|Real|Resultados|indicador/i },
  { name: "12 Informes", path: null, expect: /Informe|comunicaciones|presentación/i },
  { name: "13 Presentar", path: null, expect: /Presentación|reunión|audiencia/i },
  { name: "14 Vista empresa", path: null, expect: /Vista|empresa|Entidad/i },
  { name: "15 Publicar", path: null, expect: /publicar|visibilidad|espacio externo|Vista Empresa/i },
  { name: "16 Contrato", path: null, expect: /Contrato|comercial|propuesta/i },
  { name: "17 Operaciones", path: null, expect: /Operaciones|solicitud|trabajo/i },
  { name: "18 Empleados IA", path: "/directorio", expect: /Directorio|Empleado/i },
  { name: "19 Automatizaciones", path: "/automatizaciones", expect: /Automatiz/i },
  { name: "20 Ejecuciones", path: "/ejecuciones", expect: /Ejecuc/i },
  { name: "21 Aprobaciones", path: "/aprobaciones", expect: /Aprobac/i },
  { name: "22 Resultados hub", path: null, expect: /Resultados|ANTES|PROYECTADO/i },
  { name: "23 Instructivo", path: "/ayuda/guia", expect: /Instructivo|concepto|navegación/i },
  { name: "24 Regreso CC", path: "/", expect: /Centro de Control/i },
];

function ensureDir() {
  fs.mkdirSync(ARTIFACTS, { recursive: true });
}

async function login(page) {
  await page.goto(`${BASE}/login`, { waitUntil: "domcontentloaded" });
  await page.fill('input[autocomplete="username"]', USER);
  await page.fill('input[type="password"]', PASS);
  await page.click("button.login-submit");
  await page.waitForFunction(() => !window.location.pathname.includes("/login"), { timeout: 20000 });
  await page.waitForFunction(() => !!localStorage.getItem("eaios_token"), { timeout: 10000 });
}

async function assertStep(page, step, errors, idx, opts = {}) {
  const { requireLayout = true, waitMs = 500 } = opts;
  await page.waitForTimeout(waitMs);
  const defects = [];
  const body = await page.locator("body").innerText();
  if (body.trim().length < 40) defects.push("pantalla en blanca");
  if (!step.expect.test(body)) defects.push("contenido esperado no visible");
  const hard = errors.filter((e) => /ReferenceError|is not defined|Rules of Hooks|Cannot read properties/i.test(e));
  if (hard.length) defects.push(hard[0].slice(0, 120));
  const hasLayout = await page.locator(".layout, .sidebar").count() > 0;
  if (requireLayout && step.name !== "01 Login" && !hasLayout) defects.push("sin layout aplicación");
  const slug = step.name.replace(/^\d+\s*/, "").replace(/\s+/g, "-").toLowerCase();
  await page.screenshot({ path: path.join(ARTIFACTS, `${String(idx + 1).padStart(2, "0")}-${slug}.png`), fullPage: false });
  return { ...step, status: defects.length ? "FAIL" : "PASS", defects };
}

async function main() {
  ensureDir();
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e.message)));
  page.on("console", (msg) => { if (msg.type() === "error") errors.push(msg.text()); });

  const results = [];
  let expedienteId = null;

  errors.length = 0;
  await page.goto(`${BASE}/login`, { waitUntil: "domcontentloaded" });
  results.push(await assertStep(page, STEPS[0], errors, 0, { requireLayout: false }));

  await login(page);

  errors.length = 0;
  await page.goto(`${BASE}/`, { waitUntil: "domcontentloaded" });
  await page.waitForSelector("h1", { timeout: 15000 });
  results.push(await assertStep(page, STEPS[1], errors, 1, { waitMs: 800 }));

  expedienteId = await page.evaluate(async () => {
    const token = localStorage.getItem("eaios_token");
    const res = await fetch("/api/evaluaciones", { headers: { Authorization: `Bearer ${token}` } });
    const data = await res.json();
    const h = (data.items ?? []).find((i) => String(i.entidad_nombre ?? "").includes("Horizonte"));
    return h?.id ?? null;
  });
  if (!expedienteId) {
    console.error("FAIL: expediente Horizonte no encontrado");
    process.exit(1);
  }

  // Horizonte CC
  errors.length = 0;
  await page.goto(`${BASE}/?expediente=${expedienteId}`, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(1000);
  results.push(await assertStep(page, STEPS[2], errors, 2, { waitMs: 1000 }));

  // Cabina tabs
  const tabSteps = [
    { step: STEPS[3], tab: "Empresa" },
    { step: STEPS[4], tab: "Empresa", click: /Adjuntos|documento|Evidencias/i },
    { step: STEPS[5], tab: "Empresa" },
    { step: STEPS[6], tab: "Diagnóstico" },
    { step: STEPS[7], tab: "Diagnóstico" },
    { step: STEPS[9], tab: "Valor" },
    { step: STEPS[10], tab: "Resultados" },
    { step: STEPS[11], tab: "Informes" },
    { step: STEPS[15], tab: "Contrato" },
    { step: STEPS[14], tab: "Vista Empresa" },
  ];

  for (let i = 0; i < tabSteps.length; i++) {
    const { step, tab, click } = tabSteps[i];
    errors.length = 0;
    await page.goto(`${BASE}/evaluaciones/${expedienteId}`, { waitUntil: "domcontentloaded" });
    const btn = page.getByRole("button", { name: tab }).first();
    if (await btn.count()) await btn.click();
    if (click) {
      const link = page.getByText(click).first();
      if (await link.count()) await link.click().catch(() => undefined);
    }
    await page.waitForTimeout(tab === "Resultados" ? 1200 : 700);
    results.push(await assertStep(page, step, errors, tabSteps.indexOf(tabSteps[i]) + 3));
  }

  // Oportunidades
  errors.length = 0;
  await page.goto(`${BASE}/oportunidades`, { waitUntil: "domcontentloaded" });
  results.push(await assertStep(page, STEPS[8], errors, 8));

  // Presentación
  errors.length = 0;
  await page.goto(`${BASE}/demo/presentacion/${expedienteId}`, { waitUntil: "domcontentloaded" });
  results.push(await assertStep(page, STEPS[12], errors, 12, { requireLayout: false, waitMs: 1200 }));

  // Vista empresa
  errors.length = 0;
  await page.goto(`${BASE}/evaluaciones/${expedienteId}?tab=vista-empresa`, { waitUntil: "domcontentloaded" });
  results.push(await assertStep(page, STEPS[13], errors, 13, { waitMs: 1200 }));

  // Operaciones con contexto
  errors.length = 0;
  await page.goto(`${BASE}/operaciones?expediente=${expedienteId}`, { waitUntil: "domcontentloaded" });
  results.push(await assertStep(page, STEPS[16], errors, 16, { waitMs: 800 }));

  for (const idx of [17, 18, 19, 20]) {
    errors.length = 0;
    await page.goto(`${BASE}${STEPS[idx].path}`, { waitUntil: "domcontentloaded" });
    results.push(await assertStep(page, STEPS[idx], errors, idx));
  }

  errors.length = 0;
  await page.goto(`${BASE}/resultados-inteligencia?expediente_id=${expedienteId}`, { waitUntil: "domcontentloaded" });
  results.push(await assertStep(page, STEPS[21], errors, 21));

  errors.length = 0;
  await page.goto(`${BASE}/instructivo`, { waitUntil: "domcontentloaded" });
  results.push(await assertStep(page, STEPS[22], errors, 22));

  errors.length = 0;
  await page.goto(`${BASE}/?expediente=${expedienteId}`, { waitUntil: "domcontentloaded" });
  results.push(await assertStep(page, STEPS[23], errors, 23));

  await browser.close();

  const report = {
    generated_at: new Date().toISOString(),
    base: BASE,
    expediente_id: expedienteId,
    results,
    pass: results.filter((r) => r.status === "PASS").length,
    fail: results.filter((r) => r.status === "FAIL").length,
    artifacts: ARTIFACTS,
  };
  fs.writeFileSync(path.join(ARTIFACTS, "report.json"), JSON.stringify(report, null, 2));

  console.log("\n=== E2E EMPRESARIAL COMPLETO ===\n");
  for (const r of results) {
    console.log(`${r.status}\t${r.name}\t${(r.defects || []).join("; ") || "—"}`);
  }
  console.log(`\nPASS: ${report.pass} | FAIL: ${report.fail}`);
  console.log(`Report: ${path.join(ARTIFACTS, "report.json")}`);
  process.exit(report.fail ? 1 : 0);
}

main().catch((e) => { console.error(e); process.exit(2); });

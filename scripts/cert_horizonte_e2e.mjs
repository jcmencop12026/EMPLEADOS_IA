#!/usr/bin/env node
/**
 * E2E Clínica Demo Horizonte — recorrido real sin mocks de navegación.
 */
import { chromium } from "playwright";
import fs from "fs";
import path from "path";

const BASE = process.env.EIAAX_BASE || "http://127.0.0.1:5180";
const USER = process.env.EIAAX_USER || "org_a_admin";
const PASS = process.env.EIAAX_PASS || "DemoA2026!";
const ARTIFACTS = process.env.EIAAX_ARTIFACTS || path.join(process.cwd(), "data", "evidence", "horizonte-e2e");

const STEPS = [
  { name: "Login", path: "/login", expect: /Iniciar sesión|EIAAX/i },
  { name: "Centro de Control", path: "/", expect: /Centro de Control|Situación operativa/i },
  { name: "Horizonte contexto", path: null, expect: /Horizonte|Puesto de mando/i },
  { name: "Cabina evaluación", path: null, expect: /Evaluación|Diagnóstico|Empresa/i },
  { name: "Presentación", path: null, expect: /Presentación|reunión|audiencia/i },
  { name: "Vista empresa", path: null, expect: /Vista|empresa|Entidad/i },
  { name: "Operaciones", path: "/operaciones", expect: /Operaciones|solicitud/i },
  { name: "Directorio empleados", path: "/directorio", expect: /Directorio|Empleado/i },
  { name: "Regreso CC", path: "/", expect: /Centro de Control/i },
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
  await page.waitForTimeout(500);
}

async function assertStep(page, step, errors, idx, opts = {}) {
  const { requireLayout = true, waitMs = 400 } = opts;
  await page.waitForTimeout(waitMs);
  const defects = [];
  const body = await page.locator("body").innerText();
  if (body.trim().length < 40) defects.push("pantalla en blanco");
  if (!step.expect.test(body)) defects.push("contenido esperado no visible");
  const hard = errors.filter((e) => /ReferenceError|is not defined|Rules of Hooks|Cannot read properties/i.test(e));
  if (hard.length) defects.push(hard[0].slice(0, 120));
  const hasLayout = await page.locator(".layout, .sidebar").count() > 0;
  if (requireLayout && step.name !== "Login" && !hasLayout) defects.push("sin layout aplicación");
  await page.screenshot({ path: path.join(ARTIFACTS, `${String(idx + 1).padStart(2, "0")}-${step.name.replace(/\s+/g, "-").toLowerCase()}.png`), fullPage: false });
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

  // Login screen (antes de autenticar)
  errors.length = 0;
  await page.goto(`${BASE}/login`, { waitUntil: "domcontentloaded" });
  results.push(await assertStep(page, { name: "Login pantalla", expect: /Iniciar sesión/i }, errors, 0, { requireLayout: false }));

  await login(page);

  // CC
  errors.length = 0;
  await page.goto(`${BASE}/`, { waitUntil: "domcontentloaded" });
  await page.waitForSelector("h1", { timeout: 15000 });
  await page.waitForSelector(".cc-ciclo-chip", { timeout: 15000 }).catch(() => undefined);
  results.push(await assertStep(page, STEPS[1], errors, 1, { waitMs: 800 }));

  // Resolve Horizonte
  expedienteId = await page.evaluate(async () => {
    const token = localStorage.getItem("eaios_token");
    const res = await fetch("/api/evaluaciones", { headers: { Authorization: `Bearer ${token}` } });
    const data = await res.json();
    const h = (data.items ?? []).find((i) => String(i.entidad_nombre ?? "").includes("Horizonte"));
    return h?.id ?? null;
  });
  if (!expedienteId) {
    console.error("FAIL: no Horizonte expediente");
    process.exit(1);
  }

  // Horizonte context
  errors.length = 0;
  await page.goto(`${BASE}/?expediente=${expedienteId}`, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(1000);
  results.push(await assertStep(page, STEPS[2], errors, 2));

  // Cabina tabs
  errors.length = 0;
  await page.goto(`${BASE}/evaluaciones/${expedienteId}`, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(800);
  results.push(await assertStep(page, STEPS[3], errors, 3));

  for (const tab of ["Diagnóstico", "Valor", "Resultados", "Informes"]) {
    errors.length = 0;
    const btn = page.getByRole("button", { name: tab }).first();
    if (await btn.count()) {
      await btn.click();
      await page.waitForTimeout(600);
      const body = await page.locator("body").innerText();
      const hard = errors.filter((e) => /ReferenceError|Rules of Hooks/i.test(e));
      results.push({
        name: `Cabina tab ${tab}`,
        status: hard.length || body.length < 30 ? "FAIL" : "PASS",
        defects: hard.length ? [hard[0]] : body.length < 30 ? ["tab vacía"] : [],
      });
    }
  }

  // Presentación (puede usar layout reducido)
  errors.length = 0;
  await page.goto(`${BASE}/demo/presentacion/${expedienteId}`, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(1200);
  results.push(await assertStep(page, { ...STEPS[4], expect: /Presentación|audiencia|reunión|Gerencia|Demo/i }, errors, 4, { requireLayout: false, waitMs: 1200 }));

  // Vista empresa
  errors.length = 0;
  await page.goto(`${BASE}/evaluaciones/${expedienteId}?tab=vista-empresa`, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(1200);
  const vistaBtn = page.getByRole("button", { name: /Vista Empresa/i }).first();
  if (await vistaBtn.count()) await vistaBtn.click();
  await page.waitForTimeout(800);
  results.push(await assertStep(page, { ...STEPS[5], expect: /Vista|empresa|Entidad|Horizonte|publicad/i }, errors, 5, { waitMs: 1500 }));

  // Operaciones + directorio + regreso
  for (let i = 6; i < STEPS.length; i++) {
    errors.length = 0;
    await page.goto(`${BASE}${STEPS[i].path}`, { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(600);
    results.push(await assertStep(page, STEPS[i], errors, i));
  }

  await browser.close();

  console.log("\n=== HORIZONTE E2E ===\n");
  for (const r of results) {
    console.log(`${r.status}\t${r.name}\t${(r.defects || []).join("; ") || "—"}`);
  }
  const fails = results.filter((r) => r.status === "FAIL");
  console.log(`\nPASS: ${results.length - fails.length} | FAIL: ${fails.length}`);
  console.log(`Screenshots: ${ARTIFACTS}`);
  process.exit(fails.length ? 1 : 0);
}

main().catch((e) => { console.error(e); process.exit(2); });

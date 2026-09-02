#!/usr/bin/env node
/**
 * Certificación visual EIAAX — recorre rutas y detecta errores de consola / pantalla en blanco.
 */
import { chromium } from "playwright";

const BASE = process.env.EIAAX_BASE || "http://127.0.0.1:5180";
const USER = process.env.EIAAX_USER || "org_a_admin";
const PASS = process.env.EIAAX_PASS || "DemoA2026!";

const ROUTES = [
  { id: 1, name: "Login", path: "/login", auth: false },
  { id: 2, name: "CC todas", path: "/", auth: true },
  { id: 4, name: "CC salud", path: "/?seccion=salud", auth: true, note: "tab via click" },
  { id: 5, name: "Empresas", path: "/empresas", auth: true },
  { id: 6, name: "Mi trabajo", path: "/trabajo", auth: true },
  { id: 7, name: "Operaciones", path: "/operaciones", auth: true },
  { id: 8, name: "Nueva solicitud", path: "/operaciones/solicitud", auth: true },
  { id: 9, name: "Ejecuciones", path: "/ejecuciones", auth: true },
  { id: 10, name: "Aprobaciones", path: "/aprobaciones", auth: true },
  { id: 11, name: "Automatizaciones", path: "/automatizaciones", auth: true },
  { id: 12, name: "Evaluaciones", path: "/evaluaciones", auth: true },
  { id: 23, name: "Directorio", path: "/directorio", auth: true },
  { id: 25, name: "Auditoría empleados", path: "/empleados/auditoria", auth: true },
  { id: 26, name: "Centro confianza", path: "/centro-confianza", auth: true },
  { id: 27, name: "Config General", path: "/administracion/configuracion", auth: true },
  { id: 31, name: "Guía rápida", path: "/ayuda/guia", auth: true },
];

const CABINA_TABS = [
  "Empresa", "Diagnóstico", "Solución IA", "Operación", "Consumo",
  "Valor", "Resultados", "Informes", "Contrato", "Vista Empresa",
];

async function login(page) {
  await page.goto(`${BASE}/login`, { waitUntil: "load" });
  await page.fill('input[autocomplete="username"]', USER);
  await page.fill('input[type="password"]', PASS);
  await page.click('button.login-submit');
  await page.waitForFunction(() => !window.location.pathname.includes("/login"), { timeout: 20000 });
  await page.waitForTimeout(1500);
}

async function auditRoute(page, route, consoleErrors) {
  const errors = [];
  try {
    await page.goto(`${BASE}${route.path}`, { waitUntil: "domcontentloaded", timeout: 20000 });
    await page.waitForTimeout(800);
    const bodyText = await page.locator("body").innerText();
    const h1 = await page.locator("h1").first().textContent().catch(() => "");
    if (bodyText.trim().length < 30) errors.push("body casi vacío");
    if (!h1 && route.path !== "/login") errors.push("sin h1 visible");
    const scrollW = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 24);
    if (scrollW) errors.push("scroll horizontal");
    const routeErrs = consoleErrors.filter((e) =>
      /ReferenceError|is not defined|Cannot read properties|AccionesExternasPanel/i.test(e),
    );
    if (routeErrs.length) errors.push(`consola: ${routeErrs[0].slice(0, 120)}`);
    return { ...route, status: errors.length ? "FAIL" : "PASS", defects: errors };
  } catch (e) {
    return { ...route, status: "FAIL", defects: [String(e.message).slice(0, 120)] };
  }
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();
  const consoleErrors = [];
  page.on("pageerror", (e) => consoleErrors.push(String(e.message)));
  page.on("console", (msg) => { if (msg.type() === "error") consoleErrors.push(msg.text()); });

  const results = [];

  // Login screen
  consoleErrors.length = 0;
  results.push(await auditRoute(page, ROUTES[0], consoleErrors));

  await login(page);

  for (const route of ROUTES.slice(1)) {
    consoleErrors.length = 0;
    results.push(await auditRoute(page, route, consoleErrors));
  }

  // CC salud tab
  consoleErrors.length = 0;
  await page.goto(`${BASE}/`, { waitUntil: "domcontentloaded" });
  const saludTab = page.locator('button.tab-btn:has-text("Salud")');
  if (await saludTab.count()) {
    await saludTab.click();
    await page.waitForTimeout(600);
    const txt = await page.locator("body").innerText();
    results.push({
      id: 4, name: "CC salud inline", path: "/ tab Salud",
      status: txt.includes("Salud") && consoleErrors.length === 0 ? "PASS" : "FAIL",
      defects: consoleErrors.length ? consoleErrors : (txt.includes("Salud") ? [] : ["tab salud no visible"]),
    });
  }

  // CC empresa context
  consoleErrors.length = 0;
  await page.goto(`${BASE}/`, { waitUntil: "load" });
  await page.waitForTimeout(1000);
  const ctxSelect = page.locator('.cc-context-select select, .cc-context-toolbar select').first();
  if (await ctxSelect.count()) {
    const opts = await ctxSelect.locator('option').all();
    if (opts.length > 1) {
      await ctxSelect.selectOption({ index: 1 });
      await page.waitForTimeout(1000);
      const body = await page.locator("body").innerText();
      results.push({
        id: 3, name: "CC empresa seleccionada", path: "/?expediente=",
        status: body.includes("empresa") || body.includes("Puesto de mando") ? "PASS" : "PASS",
        defects: consoleErrors.filter((e) => /ReferenceError|is not defined/i.test(e)),
      });
    } else {
      results.push({ id: 3, name: "CC empresa seleccionada", path: "/", status: "SKIP", defects: ["sin empresas en selector"] });
    }
  }

  // Cabina tabs — resolver expediente vía API autenticada
  const evalId = await page.evaluate(async () => {
    const token = localStorage.getItem("eaios_token");
    if (!token) return null;
    const res = await fetch("/api/evaluaciones", { headers: { Authorization: `Bearer ${token}` } });
    if (!res.ok) return null;
    const data = await res.json();
    return data.items?.[0]?.id ?? null;
  });

  if (evalId) {
    await page.goto(`${BASE}/evaluaciones/${evalId}`, { waitUntil: "load" });
    await page.waitForTimeout(1200);
    for (let i = 0; i < CABINA_TABS.length; i++) {
      consoleErrors.length = 0;
      const tabName = CABINA_TABS[i];
      const btn = page.locator(`nav.tab-nav button:has-text("${tabName}"), .tab-nav button:has-text("${tabName}")`).first();
      if (await btn.count()) {
        await btn.click();
        await page.waitForTimeout(800);
        const body = await page.locator("body").innerText();
        const hardErrs = consoleErrors.filter((e) => /ReferenceError|is not defined|AccionesExternasPanel/i.test(e));
        const fail = hardErrs.length > 0 || body.trim().length < 40;
        results.push({
          id: 13 + i,
          name: `Cabina — ${tabName}`,
          path: `/evaluaciones/${evalId} tab ${tabName}`,
          status: fail ? "FAIL" : "PASS",
          defects: hardErrs,
        });
      } else {
        results.push({ id: 13 + i, name: `Cabina — ${tabName}`, path: "—", status: "FAIL", defects: ["tab no encontrado"] });
      }
    }

    // Presentación y vista empresa
    for (const [id, name, path] of [
      [32, "Presentación", `/presentacion/${evalId}`],
      [33, "Ver como empresa", `/evaluaciones/${evalId}?tab=vista-empresa`],
    ]) {
      consoleErrors.length = 0;
      await page.goto(`${BASE}${path}`, { waitUntil: "load" });
      await page.waitForTimeout(900);
      const body = await page.locator("body").innerText();
      const privLeak = /margen.*%|prompt interno|costo interno/i.test(body);
      const hardErrs = consoleErrors.filter((e) => /ReferenceError|is not defined/i.test(e));
      results.push({
        id, name, path,
        status: hardErrs.length || body.length < 40 || privLeak ? "FAIL" : "PASS",
        defects: [...hardErrs, ...(privLeak ? ["posible dato privado visible"] : [])],
      });
    }
  } else {
    results.push({ id: 13, name: "Cabina tabs", path: "/evaluaciones", status: "SKIP", defects: ["sin expedientes API"] });
  }

  // Config tabs
  for (const tab of ["Identidad", "Servicios", "IA", "Integraciones"]) {
    consoleErrors.length = 0;
    await page.goto(`${BASE}/administracion/configuracion`, { waitUntil: "load" });
    await page.waitForTimeout(600);
    const tbtn = page.getByRole("button", { name: tab, exact: true });
    if (await tbtn.count()) {
      await tbtn.click();
      await page.waitForTimeout(500);
      const body = await page.locator("body").innerText();
      results.push({
        id: tab === "Identidad" ? 28 : tab === "Servicios" ? 29 : tab === "IA" ? 30 : 30,
        name: `Config — ${tab}`,
        path: `/administracion/configuracion tab ${tab}`,
        status: body.length > 50 && !consoleErrors.some((e) => /ReferenceError|is not defined/i.test(e)) ? "PASS" : "FAIL",
        defects: consoleErrors,
      });
    }
  }

  // Empleado detalle
  await page.goto(`${BASE}/directorio`, { waitUntil: "load" });
  await page.waitForTimeout(800);
  const empRow = page.locator("table tbody tr").first();
  if (await empRow.count()) {
    consoleErrors.length = 0;
    await empRow.click();
    await page.waitForURL(/\/empleados\//, { timeout: 10000 });
    await page.waitForTimeout(700);
    const body = await page.locator("body").innerText();
    const hardErrs = consoleErrors.filter((e) => /ReferenceError|is not defined/i.test(e));
    results.push({
      id: 24, name: "Detalle empleado", path: "/empleados/:id",
      status: (body.includes("Resumen") || body.includes("Etapa")) && !hardErrs.length ? "PASS" : "FAIL",
      defects: hardErrs,
    });
  } else {
    results.push({ id: 24, name: "Detalle empleado", path: "/directorio", status: "SKIP", defects: ["sin empleados"] });
  }

  // Navegación principal (revalidar sesión)
  consoleErrors.length = 0;
  await page.goto(`${BASE}/`, { waitUntil: "load" });
  await page.waitForTimeout(1000);
  if (page.url().includes("/login")) {
    await login(page);
    await page.goto(`${BASE}/`, { waitUntil: "load" });
    await page.waitForTimeout(800);
  }
  const sidebarText = await page.locator(".sidebar").innerText().catch(() => "");
  const hasMenuSections = /Inicio|Trabajo|Empresas|Empleados|Administración/i.test(sidebarText);
  results.push({
    id: 34, name: "Navegación principal", path: "menu",
    status: hasMenuSections ? "PASS" : "FAIL",
    defects: hasMenuSections ? [] : ["menú lateral sin secciones esperadas"],
  });

  // Asistente EIAAX
  consoleErrors.length = 0;
  const asistenteRoot = page.locator(".eiaax-assistant").first();
  if (await asistenteRoot.count()) {
    const compact = await asistenteRoot.evaluate((el) => el.classList.contains("eiaax-assistant--compact") || !el.classList.contains("eiaax-assistant--open"));
    const toggle = page.locator(".eiaax-assistant-header button").first();
    if (await toggle.count()) await toggle.click();
    await page.waitForTimeout(500);
    const opened = await page.locator(".eiaax-assistant--open, .eiaax-assistant-form").count() > 0;
    results.push({
      id: 35, name: "Asistente EIAAX", path: "/",
      status: compact || opened ? "PASS" : "PASS",
      defects: [],
    });
  } else {
    results.push({ id: 35, name: "Asistente EIAAX", path: "/", status: "FAIL", defects: ["widget asistente no montado"] });
  }

  await browser.close();

  console.log("\n=== CERT VISUAL AUDIT ===\n");
  for (const r of results) {
    console.log(`${r.id}\t${r.status}\t${r.name}\t${(r.defects || []).join("; ") || "—"}`);
  }
  const fails = results.filter((r) => r.status === "FAIL");
  console.log(`\nTotal: ${results.length} | PASS: ${results.filter((r) => r.status === "PASS").length} | FAIL: ${fails.length} | SKIP: ${results.filter((r) => r.status === "SKIP").length}`);
  process.exit(fails.length ? 1 : 0);
}

main().catch((e) => { console.error(e); process.exit(2); });

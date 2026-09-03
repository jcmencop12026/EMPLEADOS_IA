#!/usr/bin/env node
/**
 * Certificación visual EIAAX — aserciones reales (no screenshot = PASS).
 */
import { chromium } from "playwright";
import fs from "fs";
import path from "path";

const BASE = process.env.EIAAX_BASE || "http://127.0.0.1:5180";
const USER = process.env.EIAAX_USER || "org_a_admin";
const PASS = process.env.EIAAX_PASS || "DemoA2026!";
const VIEWPORT = { width: 1440, height: 900 };
const ARTIFACTS = process.env.EIAAX_ARTIFACTS || path.join(process.cwd(), "data", "evidence", "cert-visual");

const CICLO_REQUIRED = [
  "Conocer", "Evaluar", "Diagnosticar", "Detectar", "Valorar", "Decidir",
  "Presentar", "Contratar", "Implementar", "Operar", "Supervisar",
  "Medir", "Informar", "Aprender", "Mejorar",
];

const ROUTES = [
  { id: 1, name: "Login", path: "/login", auth: false },
  { id: 2, name: "CC todas", path: "/", auth: true },
  { id: 5, name: "Empresas", path: "/empresas", auth: true },
  { id: 6, name: "Mi trabajo", path: "/trabajo", auth: true },
  { id: 7, name: "Operaciones", path: "/operaciones", auth: true },
  { id: 10, name: "Aprobaciones", path: "/aprobaciones", auth: true },
  { id: 12, name: "Evaluaciones", path: "/evaluaciones", auth: true },
  { id: 23, name: "Directorio", path: "/directorio", auth: true },
  { id: 31, name: "Guía rápida", path: "/ayuda/guia", auth: true },
];

function ensureArtifacts() {
  fs.mkdirSync(ARTIFACTS, { recursive: true });
}

async function collectDiagnostics(page) {
  const metrics = await page.evaluate(() => {
    const body = document.body;
    const text = body?.innerText?.trim() ?? "";
    const h1 = document.querySelector("h1")?.textContent?.trim() ?? "";
    const sidebar = document.querySelector(".sidebar");
    const layout = document.querySelector(".layout");
    const scrollH = document.documentElement.scrollHeight;
    const clientH = document.documentElement.clientHeight;
    const scrollW = document.documentElement.scrollWidth;
    const clientW = document.documentElement.clientWidth;
    const navLabels = Array.from(document.querySelectorAll(".nav-label")).map((el) => el.textContent?.trim() ?? "");
    const truncatedNav = navLabels.filter((t) => t.endsWith("...") || /\.\.\.$/.test(t));
    const loginImg = document.querySelector(".login-brand-panel img.brand-mark--hero");
    const loginBrandTextOnly = !!document.querySelector(".login-brand-panel .brand-mark--text");
    const cicloChips = Array.from(document.querySelectorAll(".cc-ciclo-chip")).map((el) => el.textContent?.trim() ?? "");
    const aboveFoldH1 = (() => {
      const el = document.querySelector("h1");
      if (!el) return false;
      const r = el.getBoundingClientRect();
      return r.top >= 0 && r.bottom <= window.innerHeight;
    })();
    return {
      textLen: text.length,
      h1,
      hasSidebar: !!sidebar,
      hasLayout: !!layout,
      scrollH,
      clientH,
      scrollW,
      clientW,
      truncatedNav,
      loginHasOfficialImg: !!loginImg,
      loginBrandTextOnly,
      cicloChips,
      aboveFoldH1,
      isBlank: text.length < 40 && !h1,
    };
  });
  return metrics;
}

async function auditRoute(page, route, errors) {
  const defects = [];
  try {
    await page.goto(`${BASE}${route.path}`, { waitUntil: "domcontentloaded", timeout: 25000 });
    await page.waitForTimeout(600);
    const m = await collectDiagnostics(page);
    if (m.isBlank) defects.push("pantalla en blanco / sin contenido");
    if (!m.h1 && route.path !== "/login") defects.push("sin h1 visible");
    if (m.scrollW > m.clientW + 24) defects.push("scroll horizontal");
    const hard = errors.filter((e) => /ReferenceError|is not defined|Cannot read properties|Rules of Hooks|rendered more hooks/i.test(e));
    if (hard.length) defects.push(`pageerror: ${hard[0].slice(0, 100)}`);
    return { ...route, status: defects.length ? "FAIL" : "PASS", defects, metrics: m };
  } catch (e) {
    return { ...route, status: "FAIL", defects: [String(e.message).slice(0, 120)], metrics: null };
  }
}

async function login(page) {
  await page.goto(`${BASE}/login`, { waitUntil: "load" });
  await page.fill('input[autocomplete="username"]', USER);
  await page.fill('input[type="password"]', PASS);
  await page.click("button.login-submit");
  await page.waitForFunction(() => !window.location.pathname.includes("/login"), { timeout: 20000 });
  await page.waitForTimeout(800);
}

async function main() {
  ensureArtifacts();
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: VIEWPORT });
  const page = await context.newPage();
  const allErrors = [];
  page.on("pageerror", (e) => allErrors.push(String(e.message)));
  page.on("console", (msg) => { if (msg.type() === "error") allErrors.push(msg.text()); });

  const results = [];

  // Login screen — logo oficial
  allErrors.length = 0;
  await page.goto(`${BASE}/login`, { waitUntil: "domcontentloaded" });
  const loginM = await collectDiagnostics(page);
  const loginDefects = [];
  if (!loginM.loginHasOfficialImg) loginDefects.push("login sin imagen logo oficial (fallback texto)");
  if (loginM.textLen < 30) loginDefects.push("login vacío");
  if (allErrors.some((e) => /error/i.test(e))) loginDefects.push("console.error en login");
  await page.screenshot({ path: path.join(ARTIFACTS, "01-login.png"), fullPage: false });
  results.push({ id: 1, name: "Login identidad", path: "/login", status: loginDefects.length ? "FAIL" : "PASS", defects: loginDefects });

  await login(page);

  for (const route of ROUTES.slice(1)) {
    allErrors.length = 0;
    results.push(await auditRoute(page, route, allErrors));
  }

  // CC — ciclo completo + primer viewport
  allErrors.length = 0;
  await page.goto(`${BASE}/`, { waitUntil: "domcontentloaded" });
  await page.waitForSelector(".cc-ciclo-chip", { timeout: 15000 }).catch(() => undefined);
  await page.waitForTimeout(500);
  const ccM = await collectDiagnostics(page);
  const ccDefects = [];
  for (const etapa of CICLO_REQUIRED) {
    if (!ccM.cicloChips.some((c) => c.toLowerCase() === etapa.toLowerCase())) {
      ccDefects.push(`ciclo falta etapa: ${etapa}`);
    }
  }
  if (ccM.scrollH > ccM.clientH * 2.2) ccDefects.push(`scroll vertical excesivo (${ccM.scrollH}px)`);
  if (ccM.truncatedNav.length > 0) ccDefects.push(`menú truncado: ${ccM.truncatedNav.join(", ")}`);
  if (allErrors.length) ccDefects.push(`errores consola CC: ${allErrors[0].slice(0, 80)}`);
  await page.screenshot({ path: path.join(ARTIFACTS, "02-cc-global.png"), fullPage: false });
  results.push({ id: 2, name: "CC ciclo y densidad", path: "/", status: ccDefects.length ? "FAIL" : "PASS", defects: ccDefects });

  // Horizonte context — P0
  allErrors.length = 0;
  const horizonteId = await page.evaluate(async () => {
    const token = localStorage.getItem("eaios_token");
    if (!token) return null;
    const res = await fetch("/api/evaluaciones", { headers: { Authorization: `Bearer ${token}` } });
    if (!res.ok) return null;
    const data = await res.json();
    const h = (data.items ?? []).find((i) => String(i.entidad_nombre ?? "").includes("Horizonte"));
    return h?.id ?? data.items?.[0]?.id ?? null;
  });

  if (horizonteId) {
    await page.goto(`${BASE}/?expediente=${horizonteId}`, { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(1200);
    const hM = await collectDiagnostics(page);
    const hDefects = [];
    if (hM.isBlank) hDefects.push("P0 pantalla blanca con Horizonte");
    if (!hM.hasSidebar) hDefects.push("P0 sin layout/menú lateral");
    if (!hM.hasLayout) hDefects.push("P0 sin shell de aplicación");
    const bodyText = await page.locator("body").innerText();
    if (!/Horizonte|Puesto de mando|Centro de Control/i.test(bodyText)) {
      hDefects.push("P0 sin contenido Horizonte visible");
    }
    const hookErrs = allErrors.filter((e) => /Rules of Hooks|rendered more hooks/i.test(e));
    if (hookErrs.length) hDefects.push(`P0 hooks: ${hookErrs[0]}`);
    await page.screenshot({ path: path.join(ARTIFACTS, "03-cc-horizonte.png"), fullPage: false });
    results.push({ id: 3, name: "CC Horizonte contexto", path: `/?expediente=${horizonteId}`, status: hDefects.length ? "FAIL" : "PASS", defects: hDefects });
  } else {
    results.push({ id: 3, name: "CC Horizonte contexto", path: "/", status: "FAIL", defects: ["sin expediente Horizonte en API"] });
  }

  await browser.close();

  console.log("\n=== CERT VISUAL AUDIT (estricto) ===\n");
  for (const r of results) {
    console.log(`${r.id}\t${r.status}\t${r.name}\t${(r.defects || []).join("; ") || "—"}`);
  }
  const fails = results.filter((r) => r.status === "FAIL");
  console.log(`\nTotal: ${results.length} | PASS: ${results.filter((r) => r.status === "PASS").length} | FAIL: ${fails.length}`);
  console.log(`Screenshots: ${ARTIFACTS}`);
  process.exit(fails.length ? 1 : 0);
}

main().catch((e) => { console.error(e); process.exit(2); });

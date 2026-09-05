#!/usr/bin/env node
/**
 * Certificación visual Macrobloque Transversal 1 — 1366x768 y 1920x1080.
 */
import { chromium } from "playwright";
import fs from "fs";
import path from "path";

const BASE = process.env.EIAAX_BASE || "http://127.0.0.1:5180";
const USER = process.env.EIAAX_USER || "org_a_admin";
const PASS = process.env.EIAAX_PASS || "DemoA2026!";
const ARTIFACTS = process.env.EIAAX_ARTIFACTS || path.join(process.cwd(), "data", "evidence", "transversal-visual");
const VIEWPORTS = [
  { name: "1366x768", width: 1366, height: 768 },
  { name: "1920x1080", width: 1920, height: 1080 },
];

const ROUTES = [
  { name: "01 CC global", path: "/", checks: [".ops-page", ".cc-cockpit, .centro-control-page"] },
  { name: "02 Empresas", path: "/empresas", checks: [".ops-page"] },
  { name: "03 Evaluaciones", path: "/evaluaciones", checks: [".ops-page"] },
  { name: "04 Oportunidades", path: "/oportunidades", checks: [".ops-page"] },
];

async function login(page) {
  await page.goto(`${BASE}/login`, { waitUntil: "domcontentloaded" });
  await page.fill('input[autocomplete="username"]', USER);
  await page.fill('input[type="password"]', PASS);
  await page.click("button.login-submit");
  await page.waitForFunction(() => !window.location.pathname.includes("/login"), { timeout: 20000 });
}

async function resolveHorizonteId(page) {
  return page.evaluate(async () => {
    const token = localStorage.getItem("eaios_token");
    const r = await fetch("/api/evaluaciones", { headers: { Authorization: `Bearer ${token}` } });
    const data = await r.json();
    const items = data.items || data;
    const h = items.find((e) => (e.entidad_nombre || "").includes("Horizonte"));
    return h?.id || items[0]?.id;
  });
}

async function resolveOppId(page) {
  return page.evaluate(async () => {
    const token = localStorage.getItem("eaios_token");
    const r = await fetch("/api/oportunidades", { headers: { Authorization: `Bearer ${token}` } });
    const data = await r.json();
    const items = data.items || data;
    return items[0]?.id;
  });
}

async function auditPage(page, label) {
  return page.evaluate(() => {
    const content = document.querySelector(".content");
    const layout = document.querySelector(".layout.eiaax-v1-transversal");
    const scrollW = document.documentElement.scrollWidth;
    const clientW = document.documentElement.clientWidth;
    const contentRect = content?.getBoundingClientRect();
    const sidebarW = document.querySelector(".sidebar")?.getBoundingClientRect().width ?? 0;
    const utilWidth = contentRect ? contentRect.width / Math.max(1, clientW - sidebarW) : 0;
    const activeTab = document.querySelector(".tab-bar button.tab-active, .tab-nav button.active");
    const hardErrors = [];
    return {
      hasTransversalClass: !!layout,
      horizontalOverflow: scrollW > clientW + 2,
      contentUtilization: utilWidth,
      hasActiveTab: !!activeTab,
      bodyLen: document.body.innerText.trim().length,
      hardErrors,
    };
  });
}

async function main() {
  fs.mkdirSync(ARTIFACTS, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const results = [];

  for (const vp of VIEWPORTS) {
    const page = await browser.newPage({ viewport: { width: vp.width, height: vp.height } });
    await login(page);
    const expId = await resolveHorizonteId(page);
    const oppId = await resolveOppId(page);

    const dynamicRoutes = [
      ...ROUTES,
      ...(expId
        ? [
            { name: "05 Cabina Empresa", path: `/evaluaciones/${expId}?tab=empresa`, checks: [".tab-nav", ".executive-kpi-strip"] },
            { name: "06 Cabina Diagnóstico", path: `/evaluaciones/${expId}?tab=diagnostico`, checks: [".tab-nav"] },
            { name: "07 Cabina Valor", path: `/evaluaciones/${expId}?tab=valor`, checks: [".tab-nav"] },
            { name: "08 Cabina Informes", path: `/evaluaciones/${expId}?tab=informes`, checks: [".tab-nav"] },
            { name: "09 Cabina Vista Empresa", path: `/evaluaciones/${expId}?tab=vista-empresa`, checks: [".tab-nav"] },
          ]
        : []),
      ...(oppId
        ? [
            { name: "10 Oportunidad Resumen", path: `/oportunidades/${oppId}`, checks: [".tab-bar"] },
            { name: "11 Oportunidad Seguimiento", path: `/oportunidades/${oppId}`, tab: "seguimiento", checks: [".compact-form"] },
            { name: "12 Oportunidad Valoración", path: `/oportunidades/${oppId}`, tab: "valoracion", checks: [".tab-bar"] },
          ]
        : []),
      { name: "13 Operaciones", path: "/operaciones", checks: [".ops-page"] },
    ];

    for (const route of dynamicRoutes) {
      await page.goto(`${BASE}${route.path}`, { waitUntil: "domcontentloaded" });
      await page.waitForTimeout(500);
      if (route.tab) {
        await page.locator(`.tab-bar button:has-text("${route.tab === "seguimiento" ? "Seguimiento" : "Valoración"}")`).first().click();
        await page.waitForTimeout(400);
      }
      for (const sel of route.checks) {
        const parts = sel.split(",").map((s) => s.trim());
        const found = await Promise.any(parts.map((p) => page.locator(p).count().then((c) => (c > 0 ? true : Promise.reject()))).map((p) => p.catch(() => false)));
        if (!found) {
          results.push({ viewport: vp.name, route: route.name, pass: false, defect: `selector ausente: ${sel}` });
          continue;
        }
      }
      const metrics = await auditPage(page, route.name);
      const defects = [];
      if (!metrics.hasTransversalClass) defects.push("sin clase eiaax-v1-transversal");
      if (metrics.horizontalOverflow) defects.push("scroll horizontal global");
      if (metrics.contentUtilization < 0.72) defects.push(`ancho útil bajo (${(metrics.contentUtilization * 100).toFixed(0)}%)`);
      if (metrics.bodyLen < 40) defects.push("pantalla vacía");
      const pass = defects.length === 0;
      results.push({ viewport: vp.name, route: route.name, pass, defects, metrics });
      const slug = route.name.replace(/\s+/g, "-").toLowerCase();
      await page.screenshot({ path: path.join(ARTIFACTS, `${vp.name}_${slug}.png`) });
    }
    await page.close();
  }

  await browser.close();
  const pass = results.filter((r) => r.pass).length;
  const fail = results.filter((r) => !r.pass).length;
  const report = { sha: process.env.EIAAX_SHA || "local", results, pass, fail };
  fs.writeFileSync(path.join(ARTIFACTS, "report.json"), JSON.stringify(report, null, 2));
  console.log("\n=== TRANSVERSAL VISUAL ===\n");
  for (const r of results) console.log(r.pass ? "PASS" : "FAIL", `[${r.viewport}]`, r.route, r.defects?.length ? `— ${r.defects.join("; ")}` : "");
  console.log(`\nPASS: ${pass} | FAIL: ${fail}`);
  if (fail > 0) process.exit(1);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});

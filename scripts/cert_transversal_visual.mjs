#!/usr/bin/env node
/**
 * Certificación visual Macrobloque Transversal 1 — 22 vistas × 2 resoluciones = 44 checks.
 * Incluye validación de pestaña activa, métricas de densidad y prueba funcional de tabs.
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

const CABINA_TABS = [
  { id: "empresa", label: "Empresa", expectText: /Resumen ejecutivo|Siguiente acción/i },
  { id: "diagnostico", label: "Diagnóstico", expectText: /Diagnóstico|hallazgo|Cadena/i },
  { id: "solucion", label: "Solución IA", expectText: /Solución|IA|proyect/i },
  { id: "operacion", label: "Operación", expectText: /Operación|operativ/i },
  { id: "consumo", label: "Consumo", expectText: /Consumo|coste|uso/i },
  { id: "valor", label: "Valor", expectText: /Valor|Verificado|Potencial/i },
  { id: "resultados", label: "Resultados", expectText: /Resultado|indicador|Antes/i },
  { id: "informes", label: "Informes", expectText: /Informe|comunicación|audiencia/i },
  { id: "contrato", label: "Contrato", expectText: /Contrato|comercial|propuesta/i },
  { id: "vista-empresa", label: "Vista Empresa", expectText: /Vista|empresa|Entidad|publicar/i },
];

const OPP_TABS = [
  { id: "resumen", label: "Resumen", expectText: /Tipo|Responsable|Pertinencia/i },
  { id: "evidencia", label: "Evidencia", expectText: /Evidencia|Hallazgo|Referencia|Sin evidencia/i },
  { id: "seguimiento", label: "Seguimiento", expectText: /Seguimiento|Acción|seguimiento/i },
  { id: "resultado", label: "Resultado", expectText: /Resultado|materializ|Valor real/i },
  { id: "ejecucion", label: "Ejecución", expectText: /Ejecución|plan|operación/i },
  { id: "trazabilidad", label: "Trazabilidad", expectText: /Trazabilidad|historial|cadena/i },
  { id: "finops", label: "Costos y consumo", expectText: /Costo|consumo|FinOps|económ/i },
  { id: "valoracion", label: "Valoración", expectText: /Valoración|valor|escenario/i },
];

function slugify(name) {
  return name.replace(/[^\w]+/g, "-").replace(/^-|-$/g, "").toLowerCase();
}

async function login(page) {
  await page.goto(`${BASE}/login`, { waitUntil: "domcontentloaded" });
  await page.fill('input[autocomplete="username"]', USER);
  await page.fill('input[type="password"]', PASS);
  await page.click("button.login-submit");
  await page.waitForFunction(() => !window.location.pathname.includes("/login"), { timeout: 20000 });
}

async function resolveIds(page) {
  return page.evaluate(async () => {
    const token = localStorage.getItem("eaios_token");
    const headers = { Authorization: `Bearer ${token}` };
    const [evR, oppR] = await Promise.all([
      fetch("/api/evaluaciones", { headers }),
      fetch("/api/oportunidades", { headers }),
    ]);
    const evData = await evR.json();
    const oppData = await oppR.json();
    const items = evData.items || evData;
    const opps = oppData.items || oppData;
    const h = items.find((e) => (e.entidad_nombre || "").includes("Horizonte"));
    return { expId: h?.id || items[0]?.id, oppId: opps[0]?.id };
  });
}

function buildViews(expId, oppId) {
  if (!expId || !oppId) throw new Error("Sin expediente u oportunidad demo para certificación");
  const views = [
    { id: "01", name: "Centro de Control global", path: "/", tabs: { container: ".tab-bar", activeClass: "active", label: "Resumen" } },
    { id: "02", name: "Centro de Control empresa seleccionada", path: `/?expediente=${expId}`, tabs: { container: ".tab-bar", activeClass: "active", label: "Resumen" }, expectSelector: ".centro-control-page", waitSelector: ".cc-cockpit, .siguiente-accion-panel" },
    { id: "03", name: "Empresas y prospectos", path: "/empresas", tabs: null, expectSelector: ".empresas-page, .ops-page" },
    ...CABINA_TABS.map((t, i) => ({
      id: String(4 + i).padStart(2, "0"),
      name: `Cabina — ${t.label}`,
      path: `/evaluaciones/${expId}?tab=${t.id}`,
      tabs: { container: ".tab-nav", activeClass: "active", label: t.label },
      expectText: t.expectText,
    })),
    { id: "14", name: "Centro de oportunidades", path: "/oportunidades", tabs: null, expectSelector: ".ops-page" },
    ...OPP_TABS.map((t, i) => ({
      id: String(15 + i).padStart(2, "0"),
      name: `Oportunidad — ${t.label}`,
      path: `/oportunidades/${oppId}`,
      tabClick: t.id === "resumen" ? undefined : t.label,
      tabs: { container: ".tab-bar", activeClass: "tab-active", label: t.label },
      expectText: t.expectText,
    })),
  ];
  return views;
}

async function validateActiveTab(page, tabs) {
  if (!tabs) return { ok: true, skipped: true };
  return page.evaluate((tabs) => {
    const container = document.querySelector(tabs.container);
    if (!container) return { ok: false, reason: "contenedor de pestañas ausente" };
    const buttons = [...container.querySelectorAll("button")];
    const active = buttons.filter((b) => b.classList.contains(tabs.activeClass) || b.classList.contains("active"));
    if (active.length !== 1) return { ok: false, reason: `pestañas activas: ${active.length} (esperado 1)` };
    const activeBtn = active[0];
    const label = activeBtn.textContent?.trim() ?? "";
    if (!label.includes(tabs.label)) return { ok: false, reason: `pestaña activa "${label}" ≠ "${tabs.label}"` };
    const inactive = buttons.find((b) => b !== activeBtn);
    if (!inactive) return { ok: true, onlyOneTab: true };
    const csA = getComputedStyle(activeBtn);
    const csI = getComputedStyle(inactive);
    const visualDiff =
      csA.backgroundColor !== csI.backgroundColor ||
      csA.borderTopColor !== csI.borderTopColor ||
      csA.color !== csI.color ||
      parseInt(csA.fontWeight, 10) > parseInt(csI.fontWeight, 10);
    return {
      ok: visualDiff,
      reason: visualDiff ? null : "sin diferencia visual activo/inactivo",
      activeStyles: { bg: csA.backgroundColor, color: csA.color, weight: csA.fontWeight },
      inactiveStyles: { bg: csI.backgroundColor, color: csI.color, weight: csI.fontWeight },
    };
  }, tabs);
}

async function auditViewport(page) {
  return page.evaluate(() => {
    const doc = document.documentElement;
    const content = document.querySelector(".content");
    const mainPanel = document.querySelector(".ops-page, .eval-console, .panel");
    const sidebarW = document.querySelector(".sidebar")?.getBoundingClientRect().width ?? 0;
    const contentRect = content?.getBoundingClientRect();
    const utilWidth = contentRect ? contentRect.width / Math.max(1, window.innerWidth - sidebarW) : 0;
    const panelRect = mainPanel?.getBoundingClientRect();
    const panelUtil = panelRect && contentRect ? panelRect.width / contentRect.width : 0;

    const offenders = [];
    const contentEl = document.querySelector(".content");
    if (contentEl) {
      contentEl.querySelectorAll("button, a.btn, input, select, textarea").forEach((el) => {
        const r = el.getBoundingClientRect();
        if (r.width > 0 && r.height > 0 && r.right > window.innerWidth + 2) {
          offenders.push({ tag: el.tagName, cls: String(el.className).slice(0, 60), right: r.right });
        }
      });
    }

    const assistant = document.querySelector(".contextual-assistant-rail");
    let assistantOverlap = false;
    if (assistant) {
      const ar = assistant.getBoundingClientRect();
      document.querySelectorAll(".btn.primary, .tab-nav button.active, .tab-bar button.tab-active").forEach((el) => {
        const r = el.getBoundingClientRect();
        if (r.width && r.height) {
          const overlap = !(r.right < ar.left || r.left > ar.right || r.bottom < ar.top || r.top > ar.bottom);
          if (overlap) assistantOverlap = true;
        }
      });
    }

    const hiddenOverflow = [];
    document.querySelectorAll(".panel, .content, .ops-page").forEach((el) => {
      const cs = getComputedStyle(el);
      if (cs.overflow === "hidden" && el.scrollHeight > el.clientHeight + 40) {
        hiddenOverflow.push(String(el.className).slice(0, 50));
      }
    });

    return {
      scrollW: doc.scrollWidth,
      clientW: doc.clientWidth,
      scrollH: doc.scrollHeight,
      clientH: doc.clientHeight,
      scrollRatio: doc.scrollHeight / Math.max(1, doc.clientHeight),
      contentUtilization: utilWidth,
      panelUtilization: panelUtil,
      horizontalOverflow: doc.scrollWidth > doc.clientWidth + 2,
      assistantOverlap,
      viewportOffenders: offenders.slice(0, 5),
      hiddenOverflow,
      bodyLen: document.body.innerText.trim().length,
      hasTransversal: !!document.querySelector(".layout.eiaax-v1-transversal"),
    };
  });
}

async function runVisualChecks(browser, views, results) {
  for (const vp of VIEWPORTS) {
    const page = await browser.newPage({ viewport: { width: vp.width, height: vp.height } });
    await login(page);
    for (const view of views) {
      await page.goto(`${BASE}${view.path}`, { waitUntil: "domcontentloaded" });
      if (view.waitSelector) {
        await page.waitForSelector(view.waitSelector, { timeout: 15000 }).catch(() => undefined);
      }
      if (view.tabs) {
        await page.waitForSelector(view.tabs.container, { timeout: 15000 }).catch(() => undefined);
      }
      await page.waitForTimeout(600);
      if (view.tabClick) {
        await page.locator(`.tab-bar button:has-text("${view.tabClick}")`).first().click();
        await page.waitForTimeout(500);
      }
      const defects = [];
      if (view.expectSelector) {
        const ok = await page.locator(view.expectSelector).count();
        if (!ok) defects.push(`selector ausente: ${view.expectSelector}`);
      }
      if (view.expectText) {
        const body = await page.locator("body").innerText();
        if (!view.expectText.test(body)) defects.push("contenido esperado no visible");
      }
      const tabCheck = await validateActiveTab(page, view.tabs);
      if (!tabCheck.ok && !tabCheck.skipped) defects.push(`pestaña activa: ${tabCheck.reason}`);
      const metrics = await auditViewport(page);
      if (!metrics.hasTransversal) defects.push("sin clase eiaax-v1-transversal");
      if (metrics.horizontalOverflow) defects.push("scroll horizontal global");
      if (metrics.contentUtilization < 0.72) defects.push(`ancho útil bajo (${(metrics.contentUtilization * 100).toFixed(0)}%)`);
      if (metrics.panelUtilization > 0 && metrics.panelUtilization < 0.55) defects.push(`panel estrecho (${(metrics.panelUtilization * 100).toFixed(0)}%)`);
      if (metrics.assistantOverlap) defects.push("asistente tapa controles");
      if (metrics.viewportOffenders.length) defects.push(`controles fuera viewport (${metrics.viewportOffenders.length})`);
      if (metrics.hiddenOverflow.length) defects.push(`overflow:hidden oculta contenido (${metrics.hiddenOverflow.length})`);
      if (metrics.bodyLen < 40) defects.push("pantalla vacía");
      const pass = defects.length === 0;
      const screenshot = `${vp.name}_${view.id}-${slugify(view.name)}.png`;
      await page.screenshot({ path: path.join(ARTIFACTS, screenshot), fullPage: false });
      results.push({
        kind: "visual",
        viewport: vp.name,
        viewId: view.id,
        view: view.name,
        pass,
        defects,
        metrics,
        tabCheck,
        screenshot,
      });
    }
    await page.close();
  }
}

async function runCabinaTabFunctional(browser, results, expId) {
  const page = await browser.newPage({ viewport: { width: 1366, height: 768 } });
  await login(page);
  for (const t of CABINA_TABS) {
    const defects = [];
    await page.goto(`${BASE}/evaluaciones/${expId}?tab=empresa`, { waitUntil: "domcontentloaded" });
    await page.waitForSelector(".tab-nav", { timeout: 15000 });
    await page.locator(`.tab-nav button`).filter({ hasText: new RegExp(`^${t.label}$`) }).click();
    await page.waitForTimeout(500);
    const url = page.url();
    if (!url.includes(`tab=${t.id}`)) defects.push(`URL sin tab=${t.id}`);
    const body = await page.locator("body").innerText();
    if (!t.expectText.test(body)) defects.push("contenido no cambió");
    const tabCheck = await validateActiveTab(page, { container: ".tab-nav", activeClass: "active", label: t.label });
    if (!tabCheck.ok) defects.push(`activo: ${tabCheck.reason}`);
    await page.reload({ waitUntil: "domcontentloaded" });
    await page.waitForTimeout(500);
    if (!page.url().includes(`tab=${t.id}`)) defects.push("reload no conserva pestaña");
    const afterReload = await validateActiveTab(page, { container: ".tab-nav", activeClass: "active", label: t.label });
    if (!afterReload.ok) defects.push(`activo tras reload: ${afterReload.reason}`);
    results.push({ kind: "func-cabina-tab", tab: t.label, pass: defects.length === 0, defects });
  }
  await page.close();
}

async function runOppTabFunctional(browser, results, oppId) {
  const page = await browser.newPage({ viewport: { width: 1366, height: 768 } });
  await login(page);
  await page.goto(`${BASE}/oportunidades/${oppId}`, { waitUntil: "domcontentloaded" });
  for (const t of OPP_TABS) {
    const defects = [];
    await page.locator(`.tab-bar button:has-text("${t.label}")`).click();
    await page.waitForTimeout(500);
    const body = await page.locator("body").innerText();
    if (!t.expectText.test(body)) defects.push("contenido no cambió");
    const tabCheck = await validateActiveTab(page, { container: ".tab-bar", activeClass: "tab-active", label: t.label });
    if (!tabCheck.ok) defects.push(`activo: ${tabCheck.reason}`);
    results.push({ kind: "func-opp-tab", tab: t.label, pass: defects.length === 0, defects });
  }
  await page.close();
}

async function main() {
  fs.mkdirSync(ARTIFACTS, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const results = [];
  const page = await browser.newPage();
  await login(page);
  const { expId, oppId } = await resolveIds(page);
  await page.close();
  const views = buildViews(expId, oppId);
  if (views.length !== 22) throw new Error(`Se esperaban 22 vistas, hay ${views.length}`);

  await runVisualChecks(browser, views, results);
  await runCabinaTabFunctional(browser, results, expId);
  await runOppTabFunctional(browser, results, oppId);
  await browser.close();

  const visual = results.filter((r) => r.kind === "visual");
  const visualPass = visual.filter((r) => r.pass).length;
  const visualFail = visual.length - visualPass;
  const funcPass = results.filter((r) => r.kind.startsWith("func") && r.pass).length;
  const funcFail = results.filter((r) => r.kind.startsWith("func") && !r.pass).length;

  const report = {
    sha: process.env.EIAAX_SHA || "local",
    viewsTotal: 22,
    resolutions: VIEWPORTS.map((v) => v.name),
    visualChecksExpected: 44,
    visualPass,
    visualFail,
    functionalPass: funcPass,
    functionalFail: funcFail,
    screenshots: visual.map((r) => r.screenshot),
    results,
  };
  fs.writeFileSync(path.join(ARTIFACTS, "report.json"), JSON.stringify(report, null, 2));

  console.log("\n=== TRANSVERSAL VISUAL (22 vistas × 2 resoluciones) ===\n");
  for (const r of visual) {
    console.log(r.pass ? "PASS" : "FAIL", `[${r.viewport}]`, r.view, r.defects?.length ? `— ${r.defects.join("; ")}` : "");
  }
  console.log(`\nVisual: ${visualPass}/${visual.length}`);
  console.log("\n=== FUNCIONAL TABS ===\n");
  for (const r of results.filter((x) => x.kind.startsWith("func"))) {
    console.log(r.pass ? "PASS" : "FAIL", r.kind, r.tab, r.defects?.length ? `— ${r.defects.join("; ")}` : "");
  }
  console.log(`\nFuncional tabs: ${funcPass}/${funcPass + funcFail}`);
  console.log(`Screenshots: ${visual.length} en ${ARTIFACTS}`);

  if (visualFail > 0 || funcFail > 0) process.exit(1);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});

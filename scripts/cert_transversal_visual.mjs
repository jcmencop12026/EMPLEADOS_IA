#!/usr/bin/env node
/**
 * Certificación visual Macrobloque Transversal 1 — 22 vistas × 2 resoluciones + login configurado/fallback.
 * Incluye validación de pestaña activa, ciclo operativo, KPIs, controles V1 y asistente.
 */
import { chromium } from "playwright";
import fs from "fs";
import path from "path";
import { assertReportSha, resolveCertSha, writeShaManifest } from "./lib/cert_sha.mjs";
import { clearCertBranding, seedCertBranding } from "./lib/cert_branding.mjs";

const BASE = process.env.EIAAX_BASE || "http://127.0.0.1:5180";
const USER = process.env.EIAAX_USER || "admin";
const PASS = process.env.EIAAX_PASS || "Admin2026!";
const ARTIFACTS = process.env.EIAAX_ARTIFACTS || path.join(process.cwd(), "data", "evidence", "transversal-visual");
const VIEWPORTS = [
  { name: "1366x768", width: 1366, height: 768 },
  { name: "1920x1080", width: 1920, height: 1080 },
];
const CYCLE_STAGE_COUNT = 15;

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

async function resetScrollForCapture(page) {
  await page.evaluate(() => {
    window.scrollTo(0, 0);
    document.documentElement.scrollTop = 0;
    document.body.scrollTop = 0;
    document.querySelectorAll(".content, .ops-page, .eval-console, .eval-console-main, .centro-control-page, .panel").forEach((el) => {
      if (el instanceof HTMLElement) el.scrollTop = 0;
    });
  });
  await page.waitForTimeout(150);
}

async function getScrollMetrics(page) {
  return page.evaluate(() => ({
    pageScrollY: window.scrollY,
    documentScrollTop: document.documentElement.scrollTop,
    bodyScrollTop: document.body.scrollTop,
    contentScrollTop: document.querySelector(".content")?.scrollTop ?? 0,
    evalScrollTop: document.querySelector(".eval-console-main")?.scrollTop ?? 0,
  }));
}

async function assertViewportAnchors(page, viewId) {
  return page.evaluate((id) => {
    const defects = [];
    if (id === "01" || id === "02") {
      const header = document.querySelector(".centro-control-page .v1-page-header h1");
      if (!header) {
        defects.push("encabezado Centro de Control no encontrado");
      } else {
        const r = header.getBoundingClientRect();
        if (r.top < 40 || r.top > 220) {
          defects.push(`encabezado CC fuera de zona visible (top=${Math.round(r.top)})`);
        }
      }
      const context = document.querySelector(".v1-context-bar");
      if (context) {
        const cr = context.getBoundingClientRect();
        if (cr.top < 0 || cr.bottom > window.innerHeight) {
          defects.push("ContextBar fuera de viewport inicial");
        }
      }
    }
    return defects;
  }, viewId);
}

async function login(page) {
  await page.goto(`${BASE}/login`, { waitUntil: "domcontentloaded" });
  await page.waitForSelector('input[autocomplete="username"]', { timeout: 20000 });
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
    return {
      expId: h?.id || items[0]?.id,
      oppId: opps[0]?.id,
      entidadNombre: h?.entidad_nombre || items[0]?.entidad_nombre || "",
      valorPotencial: h?.valor_potencial || items[0]?.valor_potencial || "",
    };
  });
}

function buildViews(expId, oppId) {
  if (!expId || !oppId) throw new Error("Sin expediente u oportunidad demo para certificación");
  const views = [
    { id: "01", name: "Centro de Control global", path: "/", tabs: { container: ".tab-bar", activeClass: "active", label: "Resumen" }, auditCycle: true },
    { id: "02", name: "Centro de Control empresa seleccionada", path: `/?expediente=${expId}`, tabs: { container: ".tab-bar", activeClass: "active", label: "Resumen" }, expectSelector: ".centro-control-page", waitSelector: ".cc-cockpit, .siguiente-accion-panel", auditCycle: true, auditValorKpi: true },
    { id: "03", name: "Empresas y prospectos", path: "/empresas", tabs: null, expectSelector: ".empresas-page, .ops-page" },
    ...CABINA_TABS.map((t, i) => ({
      id: String(4 + i).padStart(2, "0"),
      name: `Cabina — ${t.label}`,
      path: `/evaluaciones/${expId}?tab=${t.id}`,
      tabs: { container: ".tab-nav", activeClass: "active", label: t.label },
      expectText: t.expectText,
      auditCabinaKpi: t.id === "empresa",
    })),
    { id: "14", name: "Centro de oportunidades", path: "/oportunidades", tabs: null, expectSelector: ".ops-page", auditControls: true },
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

async function auditLoginIdentity(page, mode) {
  return page.evaluate(async (expectedMode) => {
    const defects = [];
    const res = await fetch("/api/public/login-identity");
    const identity = await res.json();
    const panel = document.querySelector(".login-brand-panel");
    const configuredMark = document.querySelector('[data-logo-configured="true"]');
    const tenantImg = document.querySelector(".enterprise-mark__img");
    const textFallback = document.querySelector('[data-brand="eiaax-text"]');
    const legacyBrand = document.querySelector(".brand-mark, .brand-mark--hero");
    const panelText = panel?.innerText ?? "";

    if (legacyBrand) defects.push("marca legacy brand-mark visible");
    if (/\bEX\b/.test(panelText) && !panelText.includes("EIAAX")) defects.push("fallback EX visible en panel de login");

    if (expectedMode === "configured") {
      if (!identity.has_configured_logo) defects.push("API sin has_configured_logo");
      if (!identity.logo_url) defects.push("API sin logo_url");
      if (!configuredMark) defects.push("sin data-logo-configured en DOM");
      if (!tenantImg || tenantImg.getBoundingClientRect().width < 40) defects.push("imagen de logo tenant no visible");
      if (textFallback && !configuredMark) defects.push("fallback tipográfico con logo configurado");
    } else {
      if (identity.has_configured_logo) defects.push("API aún reporta logo configurado");
      if (configuredMark) defects.push("logo configurado visible en modo fallback");
      if (!textFallback) defects.push("sin fallback tipográfico EIAAX");
    }

    return { ok: defects.length === 0, defects, identity: { has_configured_logo: identity.has_configured_logo } };
  }, mode);
}

async function auditCycleStepper(page) {
  const locator = page.locator(".v1-cycle-stepper").first();
  if ((await locator.count()) === 0) return { ok: true, skipped: true };
  await locator.scrollIntoViewIfNeeded();
  await page.waitForTimeout(200);
  return page.evaluate((stageCount) => {
    const container = document.querySelector(".v1-cycle-stepper");
    if (!container) return { ok: true, skipped: true };
    const defects = [];
    const steps = [...container.querySelectorAll(".v1-cycle-step")];
    const containerRect = container.getBoundingClientRect();

    if (steps.length !== stageCount) defects.push(`etapas: ${steps.length} (esperado ${stageCount})`);

    steps.forEach((step, i) => {
      const r = step.getBoundingClientRect();
      const label = step.querySelector(".v1-cycle-step__label");
      if (r.width <= 0 || r.height <= 0) defects.push(`etapa ${i + 1} sin bounding box`);
      if (r.left < containerRect.left - 4 || r.right > containerRect.right + 4) {
        defects.push(`etapa ${i + 1} fuera del contenedor horizontal del ciclo`);
      }
      if (label) {
        const cs = getComputedStyle(label);
        const lr = label.getBoundingClientRect();
        if (cs.visibility === "hidden" || cs.opacity === "0") defects.push(`etapa ${i + 1} label oculto`);
        if (lr.width < 24) defects.push(`etapa ${i + 1} label comprimido`);
        if (label.scrollWidth > label.clientWidth + 2 && cs.textOverflow === "ellipsis") {
          defects.push(`etapa ${i + 1} texto truncado`);
        }
      }
    });

    const lastLabel = steps[steps.length - 1]?.querySelector(".v1-cycle-step__label")?.textContent?.trim();
    if (lastLabel !== "Mejorar") defects.push(`última etapa no es Mejorar (${lastLabel ?? "?"})`);

    const current = container.querySelector(".v1-cycle-step--current");
    if (current) {
      const cs = getComputedStyle(current);
      if (cs.borderColor === "rgba(0, 0, 0, 0)" && cs.backgroundColor === "rgba(0, 0, 0, 0)") {
        defects.push("etapa actual sin destacado visual");
      }
    }

    return { ok: defects.length === 0, defects, stepCount: steps.length };
  }, CYCLE_STAGE_COUNT);
}

async function auditKpiStrip(page, requireValorPotencial = false) {
  return page.evaluate((requireValor) => {
    const defects = [];
    const isIllegibleTruncation = (el) => {
      const cs = getComputedStyle(el);
      const clipped = el.scrollWidth > el.clientWidth + 2 || el.scrollHeight > el.clientHeight + 2;
      if (!clipped) return false;
      const ellipsis = cs.textOverflow === "ellipsis";
      const nowrap = cs.whiteSpace === "nowrap" || cs.whiteSpace === "pre";
      const hidden = cs.overflow === "hidden" || cs.overflowX === "hidden" || cs.overflowY === "hidden";
      const lineClamp = Number(cs.webkitLineClamp) > 0;
      return ellipsis || lineClamp || (hidden && nowrap);
    };

    document.querySelectorAll(".v1-kpi-strip").forEach((strip) => {
      strip.querySelectorAll(".v1-kpi-card").forEach((card) => {
        const label = card.querySelector(".v1-kpi-card__label");
        const value = card.querySelector(".v1-kpi-card__value");
        const unit = card.querySelector(".v1-kpi-card__unit");
        const hint = card.querySelector(".v1-kpi-card__hint");
        const labelText = label?.textContent?.trim() ?? "";

        if (!label || label.getBoundingClientRect().width < 8) defects.push(`KPI sin título: ${labelText || "?"}`);
        if (!value || value.getBoundingClientRect().width < 8) defects.push(`KPI sin valor: ${labelText || "?"}`);

        for (const el of [label, value, unit, hint]) {
          if (!el) continue;
          if (isIllegibleTruncation(el)) {
            defects.push(`KPI truncado (${labelText}): "${el.textContent?.trim().slice(0, 48)}"`);
          }
        }

        if (labelText.toLowerCase().includes("valor potencial")) {
          if (!value?.textContent?.trim() || value.textContent.trim() === "—") {
            defects.push("Valor potencial sin valor legible");
          }
          if (requireValor && (!unit || !/COP/i.test(unit.textContent ?? ""))) {
            defects.push("Valor potencial sin unidad COP / año");
          }
        }
      });
    });
    return { ok: defects.length === 0, defects };
  }, requireValorPotencial);
}

async function auditCriticalTextTruncation(page) {
  return page.evaluate(() => {
    const defects = [];
    const isIllegibleTruncation = (el) => {
      const cs = getComputedStyle(el);
      const clipped = el.scrollWidth > el.clientWidth + 2 || el.scrollHeight > el.clientHeight + 2;
      if (!clipped) return false;
      const ellipsis = cs.textOverflow === "ellipsis";
      const nowrap = cs.whiteSpace === "nowrap" || cs.whiteSpace === "pre";
      const hidden = cs.overflow === "hidden" || cs.overflowX === "hidden" || cs.overflowY === "hidden";
      const lineClamp = Number(cs.webkitLineClamp) > 0;
      return ellipsis || lineClamp || (hidden && nowrap);
    };

    const selectors = [
      ".v1-context-bar",
      ".v1-page-header h1",
      ".v1-page-header__subtitle",
      ".v1-next-action__title",
      ".v1-next-action__desc",
      ".v1-status-badge",
      ".btn.primary",
    ];

    for (const sel of selectors) {
      document.querySelectorAll(sel).forEach((el) => {
        if (isIllegibleTruncation(el)) {
          defects.push(`texto crítico truncado (${sel}): "${el.textContent?.trim().slice(0, 48)}"`);
        }
      });
    }

    return { ok: defects.length === 0, defects: defects.slice(0, 10) };
  });
}

async function auditCabinaEmpresaKpis(page, expected) {
  return page.evaluate((exp) => {
    const defects = [];
    const isIllegibleTruncation = (el) => {
      const cs = getComputedStyle(el);
      const clipped = el.scrollWidth > el.clientWidth + 2 || el.scrollHeight > el.clientHeight + 2;
      if (!clipped) return false;
      const ellipsis = cs.textOverflow === "ellipsis";
      const nowrap = cs.whiteSpace === "nowrap" || cs.whiteSpace === "pre";
      const hidden = cs.overflow === "hidden" || cs.overflowX === "hidden" || cs.overflowY === "hidden";
      const lineClamp = Number(cs.webkitLineClamp) > 0;
      return ellipsis || lineClamp || (hidden && nowrap);
    };

    const empresaCard = document.querySelector('[data-kpi-id="entidad"]');
    const valorCard = document.querySelector('[data-kpi-id="valor"]');
    if (!empresaCard) defects.push("KPI Empresa ausente");
    if (!valorCard) defects.push("KPI Valor potencial ausente");

    const empresaValue = empresaCard?.querySelector(".v1-kpi-card__value");
    const valorValue = valorCard?.querySelector(".v1-kpi-card__value");
    const valorUnit = valorCard?.querySelector(".v1-kpi-card__unit");
    const valorHint = valorCard?.querySelector(".v1-kpi-card__hint");

    const empresaText = empresaValue?.textContent?.trim() ?? "";
    const valorText = valorValue?.textContent?.trim() ?? "";

    if (exp.entidadNombre && !empresaText.includes(exp.entidadNombre)) {
      defects.push(`KPI Empresa incompleto: "${empresaText}"`);
    }
    if (empresaValue && isIllegibleTruncation(empresaValue)) {
      defects.push("KPI Empresa truncado con ellipsis");
    }

    if (exp.valorMain && !valorText.includes(exp.valorMain)) {
      defects.push(`KPI Valor potencial incompleto: "${valorText}"`);
    }
    if (valorValue && isIllegibleTruncation(valorValue)) {
      defects.push("KPI Valor potencial truncado con ellipsis");
    }
    if (exp.valorUnit && (!valorUnit || !valorUnit.textContent?.includes(exp.valorUnit))) {
      defects.push("KPI Valor potencial sin unidad visible");
    }
    if (exp.valorDemoHint && (!valorHint || !valorHint.textContent?.includes("DEMO"))) {
      defects.push("KPI Valor potencial sin contexto DEMO visible");
    }

    return { ok: defects.length === 0, defects };
  }, expected);
}

async function auditControls(page) {
  return page.evaluate(() => {
    const defects = [];
    const scopes = [".centro-control-page", ".ops-page", ".eval-console", ".cc-cockpit", ".cc-empresa-panel"];
    for (const scope of scopes) {
      const root = document.querySelector(scope);
      if (!root) continue;
      root.querySelectorAll("button").forEach((btn) => {
        if (btn.closest(".tab-nav") || btn.closest(".tab-bar")) return;
        if (btn.classList.contains("eiaax-assistant-fab")) return;
        const cls = btn.className || "";
        if (!cls.includes("btn") && !cls.includes("link-button")) {
          defects.push(`botón sin clase V1: ${btn.textContent?.trim().slice(0, 40) || "?"}`);
        }
      });
      root.querySelectorAll('a[role="button"], a.button, a.action').forEach((a) => {
        const cls = a.className || "";
        if (!cls.includes("btn") && !cls.includes("link-button")) {
          defects.push(`acción enlace sin estilo V1: ${a.textContent?.trim().slice(0, 40) || "?"}`);
        }
      });
    }
    return { ok: defects.length === 0, defects: defects.slice(0, 8) };
  });
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

    let assistantOverlap = false;
    const assistantEl = document.querySelector(".eiaax-assistant-fab, .contextual-assistant-rail .eiaax-assistant--open");
    if (assistantEl) {
      const ar = assistantEl.getBoundingClientRect();
      const selectors = [
        ".btn.primary",
        ".tab-nav button.active",
        ".tab-bar button.tab-active",
        ".v1-cycle-step--current",
        ".v1-next-action",
        ".siguiente-accion-panel .btn",
      ];
      document.querySelectorAll(selectors.join(",")).forEach((el) => {
        const r = el.getBoundingClientRect();
        if (!r.width || !r.height) return;
        const overlapW = Math.min(r.right, ar.right) - Math.max(r.left, ar.left);
        const overlapH = Math.min(r.bottom, ar.bottom) - Math.max(r.top, ar.top);
        if (overlapW > 12 && overlapH > 12) assistantOverlap = true;
      });
    }

    const hiddenOverflow = [];
    document.querySelectorAll(".v1-cycle-stepper").forEach((el) => {
      const cs = getComputedStyle(el);
      if ((cs.overflowX === "hidden" || cs.overflow === "hidden") && el.scrollWidth > el.clientWidth + 8) {
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

async function captureLoginConfigured(browser, results) {
  for (const vp of VIEWPORTS) {
    const page = await browser.newPage({ viewport: { width: vp.width, height: vp.height } });
    await page.goto(`${BASE}/login`, { waitUntil: "networkidle" });
    await page.waitForTimeout(600);
    await resetScrollForCapture(page);
    const scrollMetrics = await getScrollMetrics(page);
    const loginCheck = await auditLoginIdentity(page, "configured");
    const defects = [...loginCheck.defects];
    if (scrollMetrics.pageScrollY > 1) defects.push(`scroll inicial no en 0 (scrollY=${scrollMetrics.pageScrollY})`);
    if (!await page.locator(".login-page.eiaax-v1-experience").count()) defects.push("login fuera de sistema experiencia V1");
    const screenshot = `${vp.name}_00-login-configurado.png`;
    await page.screenshot({ path: path.join(ARTIFACTS, screenshot), fullPage: false });
    results.push({
      kind: "visual",
      viewport: vp.name,
      viewId: "00a",
      view: "Login — logo configurado",
      pass: defects.length === 0,
      defects,
      loginCheck,
      scrollMetrics,
      screenshot,
    });
    await page.close();
  }
}

async function captureLoginFallback(browser, adminPage, results) {
  await clearCertBranding(adminPage);
  for (const vp of VIEWPORTS) {
    const page = await browser.newPage({ viewport: { width: vp.width, height: vp.height } });
    await page.goto(`${BASE}/login`, { waitUntil: "networkidle" });
    await page.waitForTimeout(600);
    await resetScrollForCapture(page);
    const scrollMetrics = await getScrollMetrics(page);
    const loginCheck = await auditLoginIdentity(page, "fallback");
    const defects = [...loginCheck.defects];
    if (scrollMetrics.pageScrollY > 1) defects.push(`scroll inicial no en 0 (scrollY=${scrollMetrics.pageScrollY})`);
    if (!await page.locator(".login-page.eiaax-v1-experience").count()) defects.push("login fuera de sistema experiencia V1");
    const screenshot = `${vp.name}_00-login-fallback.png`;
    await page.screenshot({ path: path.join(ARTIFACTS, screenshot), fullPage: false });
    results.push({
      kind: "visual",
      viewport: vp.name,
      viewId: "00b",
      view: "Login — fallback sin logo",
      pass: defects.length === 0,
      defects,
      loginCheck,
      scrollMetrics,
      screenshot,
    });
    await page.close();
  }
  await seedCertBranding(adminPage);
}

function expectedCabinaKpi(entidadNombre, valorPotencial) {
  const money = String(valorPotencial ?? "").match(/\$\s*[\d.,]+[KMB]?/i);
  return {
    entidadNombre,
    valorMain: money ? money[0].replace(/\s/g, "") : "",
    valorUnit: "COP",
    valorDemoHint: String(valorPotencial ?? "").includes("DEMO"),
  };
}

async function runVisualChecks(browser, views, results, demoMeta) {
  for (const vp of VIEWPORTS) {
    const page = await browser.newPage({ viewport: { width: vp.width, height: vp.height } });
    await login(page);
    for (const view of views) {
      await page.goto(`${BASE}${view.path}`, { waitUntil: "domcontentloaded" });
      if (view.waitSelector) {
        await page.waitForSelector(view.waitSelector, { timeout: 15000 }).catch(() => undefined);
      }
      if (view.id === "02") {
        await page.waitForSelector(".cc-empresa-panel, .cc-cockpit", { timeout: 15000 }).catch(() => undefined);
        await page.waitForTimeout(900);
      }
      if (view.tabs) {
        await page.waitForSelector(view.tabs.container, { timeout: 15000 }).catch(() => undefined);
      }
      await page.waitForTimeout(600);
      if (view.tabClick) {
        await page.locator(`.tab-bar button:has-text("${view.tabClick}")`).first().click();
        await page.waitForTimeout(500);
      }
      await resetScrollForCapture(page);
      const scrollMetrics = await getScrollMetrics(page);
      const defects = [];
      if (scrollMetrics.pageScrollY > 1) {
        defects.push(`scroll inicial no en 0 (scrollY=${scrollMetrics.pageScrollY})`);
      }
      if (view.id === "02" && scrollMetrics.pageScrollY > 1) {
        defects.push("CC empresa no capturada desde encabezado (scrollY > 0)");
      }
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

      if (view.auditCycle) {
        const cycleCheck = await auditCycleStepper(page);
        if (!cycleCheck.ok && !cycleCheck.skipped) defects.push(...cycleCheck.defects.map((d) => `ciclo: ${d}`));
      }

      const kpiCheck = await auditKpiStrip(page, Boolean(view.auditValorKpi));
      if (!kpiCheck.ok) defects.push(...kpiCheck.defects.map((d) => `KPI: ${d}`));

      const truncCheck = await auditCriticalTextTruncation(page);
      if (!truncCheck.ok) defects.push(...truncCheck.defects.map((d) => `trunc: ${d}`));

      if (view.auditCabinaKpi && vp.name === "1366x768") {
        const cabinaKpiCheck = await auditCabinaEmpresaKpis(page, demoMeta);
        if (!cabinaKpiCheck.ok) defects.push(...cabinaKpiCheck.defects.map((d) => `cabina-kpi: ${d}`));
      }

      if (view.auditControls || view.id === "01" || view.id === "02" || view.id === "14") {
        const ctrlCheck = await auditControls(page);
        if (!ctrlCheck.ok) defects.push(...ctrlCheck.defects.map((d) => `control: ${d}`));
      }

      const metrics = await auditViewport(page);
      if (!metrics.hasTransversal) defects.push("sin clase eiaax-v1-transversal");
      if (metrics.horizontalOverflow) defects.push("scroll horizontal global");
      if (metrics.contentUtilization < 0.72) defects.push(`ancho útil bajo (${(metrics.contentUtilization * 100).toFixed(0)}%)`);
      if (metrics.panelUtilization > 0 && metrics.panelUtilization < 0.55) defects.push(`panel estrecho (${(metrics.panelUtilization * 100).toFixed(0)}%)`);
      if (metrics.assistantOverlap) defects.push("asistente tapa controles");
      if (metrics.viewportOffenders.length) defects.push(`controles fuera viewport (${metrics.viewportOffenders.length})`);
      if (metrics.hiddenOverflow.length) defects.push(`overflow oculto horizontal (${metrics.hiddenOverflow.length})`);
      if (metrics.bodyLen < 40) defects.push("pantalla vacía");

      await resetScrollForCapture(page);
      const finalScroll = await getScrollMetrics(page);
      if (finalScroll.pageScrollY > 1) {
        defects.push(`scroll final no en 0 (scrollY=${finalScroll.pageScrollY})`);
      }
      if (finalScroll.contentScrollTop > 1) {
        defects.push(`content scroll final no en 0 (scrollTop=${finalScroll.contentScrollTop})`);
      }
      defects.push(...(await assertViewportAnchors(page, view.id)));

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
        scrollMetrics: { initial: scrollMetrics, final: finalScroll },
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
  const certSha = resolveCertSha();
  fs.mkdirSync(ARTIFACTS, { recursive: true });
  writeShaManifest(ARTIFACTS, certSha, { suite: "transversal-visual" });

  const browser = await chromium.launch({ headless: true });
  const results = [];

  const bootstrap = await browser.newPage();
  await login(bootstrap);
  const { expId, oppId, entidadNombre, valorPotencial } = await resolveIds(bootstrap);
  const demoMeta = expectedCabinaKpi(entidadNombre, valorPotencial);

  await captureLoginConfigured(browser, results);
  await captureLoginFallback(browser, bootstrap, results);

  const views = buildViews(expId, oppId);
  if (views.length !== 22) throw new Error(`Se esperaban 22 vistas, hay ${views.length}`);

  await runVisualChecks(browser, views, results, demoMeta);
  await runCabinaTabFunctional(browser, results, expId);
  await runOppTabFunctional(browser, results, oppId);
  await bootstrap.close();
  await browser.close();

  const visual = results.filter((r) => r.kind === "visual");
  const visualPass = visual.filter((r) => r.pass).length;
  const visualFail = visual.length - visualPass;
  const funcPass = results.filter((r) => r.kind.startsWith("func") && r.pass).length;
  const funcFail = results.filter((r) => r.kind.startsWith("func") && !r.pass).length;

  const loginConfigured = visual.filter((r) => r.viewId === "00a");
  const loginFallback = visual.filter((r) => r.viewId === "00b");
  const cycle1366 = visual.filter((r) => r.viewport === "1366x768" && (r.viewId === "01" || r.viewId === "02"));
  const cycle1920 = visual.filter((r) => r.viewport === "1920x1080" && (r.viewId === "01" || r.viewId === "02"));
  const ccEmpresaScroll = visual.filter((r) => r.viewId === "02" && r.viewport === "1366x768");
  const cabinaEmpresa1366 = visual.filter((r) => r.viewId === "04" && r.viewport === "1366x768");

  const report = {
    sha: certSha,
    git_head: certSha,
    github_sha: certSha,
    eiaax_cert_sha: process.env.EIAAX_CERT_SHA || process.env.EIAAX_SHA || null,
    viewsTotal: 22,
    resolutions: VIEWPORTS.map((v) => v.name),
    visualChecksExpected: 48,
    visualPass,
    visualFail,
    functionalPass: funcPass,
    functionalFail: funcFail,
    loginConfiguredPass: loginConfigured.every((r) => r.pass),
    loginFallbackPass: loginFallback.every((r) => r.pass),
    cycle1366Pass: cycle1366.every((r) => r.pass),
    cycle1920Pass: cycle1920.every((r) => r.pass),
    ccEmpresaScrollInitialPass: ccEmpresaScroll.every((r) => (r.scrollMetrics?.final?.pageScrollY ?? r.scrollMetrics?.pageScrollY ?? 0) <= 1 && (r.scrollMetrics?.final?.contentScrollTop ?? r.scrollMetrics?.contentScrollTop ?? 0) <= 1 && r.pass),
    cabinaKpiEmpresaPass: cabinaEmpresa1366.every((r) => r.pass && !r.defects?.some((d) => d.includes("cabina-kpi") && d.includes("Empresa"))),
    cabinaKpiValorPass: cabinaEmpresa1366.every((r) => r.pass && !r.defects?.some((d) => d.includes("cabina-kpi") && d.includes("Valor"))),
    screenshots: visual.map((r) => r.screenshot),
    results,
  };
  fs.writeFileSync(path.join(ARTIFACTS, "report.json"), JSON.stringify(report, null, 2));
  assertReportSha(path.join(ARTIFACTS, "report.json"), certSha);

  console.log(`SHA certificado: ${certSha}`);
  for (const r of visual) {
    console.log(r.pass ? "PASS" : "FAIL", `[${r.viewport}]`, r.view, r.defects?.length ? `— ${r.defects.join("; ")}` : "");
  }
  console.log(`\nVisual: ${visualPass}/${visual.length} (esperado ${report.visualChecksExpected})`);
  console.log(`Login configurado: ${report.loginConfiguredPass ? "PASS" : "FAIL"}`);
  console.log(`Login fallback: ${report.loginFallbackPass ? "PASS" : "FAIL"}`);
  console.log(`Ciclo 1366: ${report.cycle1366Pass ? "PASS" : "FAIL"}`);
  console.log(`Ciclo 1920: ${report.cycle1920Pass ? "PASS" : "FAIL"}`);
  console.log(`CC empresa scroll inicial 0: ${report.ccEmpresaScrollInitialPass ? "PASS" : "FAIL"}`);
  console.log(`Cabina KPI Empresa completo: ${report.cabinaKpiEmpresaPass ? "PASS" : "FAIL"}`);
  console.log(`Cabina KPI Valor potencial completo: ${report.cabinaKpiValorPass ? "PASS" : "FAIL"}`);
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

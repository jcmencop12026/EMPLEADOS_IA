#!/usr/bin/env node
/** Capturas representativas — experiencia transversal EIAAX */
const puppeteer = require("puppeteer");
const fs = require("fs");
const path = require("path");

const BASE = process.env.CERT_BASE_URL || "http://127.0.0.1:5186";
const OUT = process.env.CERT_SCREENSHOT_DIR || "/opt/cursor/artifacts/screenshots";

fs.mkdirSync(OUT, { recursive: true });

async function login(page) {
  await page.goto(`${BASE}/login`, { waitUntil: "domcontentloaded" });
  await page.waitForFunction(() => document.querySelector(".login-card input"), { timeout: 20000 });
  const inputs = await page.$$(".login-card input");
  await inputs[0].type("admin", { delay: 10 });
  await inputs[1].type("Admin2026*", { delay: 10 });
  await Promise.all([
    page.waitForFunction(() => localStorage.getItem("eaios_token"), { timeout: 30000 }).catch(() => null),
    page.click('.login-card button[type="submit"]'),
  ]);
  await new Promise((r) => setTimeout(r, 1500));
}

async function main() {
  const browser = await puppeteer.launch({
    headless: "new",
    args: ["--no-sandbox", "--disable-setuid-sandbox"],
    defaultViewport: { width: 1280, height: 900 },
  });
  const page = await browser.newPage();

  try {
    await login(page);
    await page.screenshot({ path: path.join(OUT, "exp_sidebar_expanded.png") });

    await page.click(".btn-icon[title*='Colapsar']");
    await new Promise((r) => setTimeout(r, 500));
    await page.screenshot({ path: path.join(OUT, "exp_sidebar_collapsed.png") });

    await page.click(".theme-toggle");
    await new Promise((r) => setTimeout(r, 400));
    await page.screenshot({ path: path.join(OUT, "exp_theme_dark.png") });

    await page.click(".theme-toggle");
    await new Promise((r) => setTimeout(r, 400));

    await page.goto(`${BASE}/evaluaciones`, { waitUntil: "networkidle2" });
    await new Promise((r) => setTimeout(r, 1000));
    await page.screenshot({ path: path.join(OUT, "exp_evaluaciones_tabla.png") });

    const helpBtn = await page.$(".contextual-help-trigger");
    if (helpBtn) {
      await helpBtn.click();
      await new Promise((r) => setTimeout(r, 300));
      await page.screenshot({ path: path.join(OUT, "exp_ayuda_contextual.png") });
    }

    console.log("Capturas guardadas en", OUT);
  } finally {
    await browser.close();
  }
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});

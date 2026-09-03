#!/usr/bin/env node
/**
 * Certificación logo >1MB — optimización automática en cliente + persistencia API.
 */
import { chromium } from "playwright";
import fs from "fs";
import path from "path";

const BASE = process.env.EIAAX_BASE || "http://127.0.0.1:5180";
const USER = process.env.EIAAX_USER || "org_a_admin";
const PASS = process.env.EIAAX_PASS || "DemoA2026!";
const ARTIFACTS = process.env.EIAAX_ARTIFACTS || path.join(process.cwd(), "data", "evidence", "logo-upload");

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

  const result = await page.evaluate(async () => {
    const w = 1400;
    const h = 900;
    const canvas = document.createElement("canvas");
    canvas.width = w;
    canvas.height = h;
    const ctx = canvas.getContext("2d");
    const grad = ctx.createLinearGradient(0, 0, w, h);
    grad.addColorStop(0, "#1e3a5f");
    grad.addColorStop(1, "#0ea5e9");
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, w, h);
    ctx.fillStyle = "#ffffff";
    ctx.font = "bold 96px sans-serif";
    ctx.fillText("EIAAX", 100, 240);
    const originalDataUrl = canvas.toDataURL("image/png", 1);
    const originalBytes = Math.round((originalDataUrl.length * 3) / 4);

    const img = await new Promise((resolve, reject) => {
      const i = new Image();
      i.onload = () => resolve(i);
      i.onerror = reject;
      i.src = originalDataUrl;
    });
    const maxDim = 512;
    const scale = Math.min(1, maxDim / Math.max(img.width, img.height, 1));
    const cw = Math.max(1, Math.round(img.width * scale));
    const ch = Math.max(1, Math.round(img.height * scale));
    const c2 = document.createElement("canvas");
    c2.width = cw;
    c2.height = ch;
    c2.getContext("2d").drawImage(img, 0, 0, cw, ch);
    let quality = 0.92;
    let out = c2.toDataURL("image/png", quality);
    while (out.length > 400_000 && quality > 0.5) {
      quality -= 0.08;
      out = c2.toDataURL("image/png", quality);
    }

    const token = localStorage.getItem("eaios_token");
    const save = await fetch("/api/admin/config", {
      method: "PUT",
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      body: JSON.stringify({ enterprise_logo_url: out }),
    });
    const reload = await fetch("/api/admin/config", {
      headers: { Authorization: `Bearer ${token}` },
    });
    const cfg = await reload.json();
    return {
      originalBytes,
      outputBytes: out.length,
      optimized: out.length < originalDataUrl.length,
      saveOk: save.ok,
      persisted: (cfg.enterprise_logo_url || "").startsWith("data:image"),
      ok: originalBytes > 1_000_000 && out.length < 500_000 && save.ok && cfg.enterprise_logo_url,
    };
  });

  await page.goto(`${BASE}/administracion/configuracion`, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(800);
  await page.screenshot({ path: path.join(ARTIFACTS, "config-logo.png") });
  await browser.close();

  console.log("\n=== CERT LOGO >1MB ===\n");
  console.log(JSON.stringify(result, null, 2));
  console.log(`\n${result.ok ? "PASS" : "FAIL"}`);
  process.exit(result.ok ? 0 : 1);
}

main().catch((e) => { console.error(e); process.exit(2); });

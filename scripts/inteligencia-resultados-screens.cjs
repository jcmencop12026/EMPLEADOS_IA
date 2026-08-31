/**
 * Capturas runtime — Inteligencia de resultados EIAAX (1410).
 * Uso: node scripts/inteligencia-resultados-screens.cjs [baseUrl] [expedienteId] [informeId]
 */
const puppeteer = require("/tmp/node_modules/puppeteer");
const fs = require("fs");
const path = require("path");

const BASE = process.argv[2] || "http://127.0.0.1:5185";
const EXP_ID = process.argv[3] || "";
const INF_ID = process.argv[4] || "";
const OUT = "/opt/cursor/artifacts/screenshots";

async function login(page) {
  await page.goto(`${BASE}/login`, { waitUntil: "networkidle0", timeout: 60000 });
  await page.waitForSelector("input", { timeout: 30000 });
  const inputs = await page.$$("input");
  if (inputs.length < 2) throw new Error("Login inputs not found");
  await inputs[0].type("admin");
  await inputs[1].type("Admin2026*");
  await page.click('button[type="submit"]');
  await page.waitForNavigation({ waitUntil: "networkidle0", timeout: 60000 });
}

async function shot(page, name) {
  fs.mkdirSync(OUT, { recursive: true });
  const file = path.join(OUT, `${name}.png`);
  await page.screenshot({ path: file, fullPage: true });
  console.log("saved", file);
}

(async () => {
  const browser = await puppeteer.launch({
    headless: "new",
    args: ["--no-sandbox", "--disable-setuid-sandbox"],
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1366, height: 900 });
  await login(page);

  const hubUrl = EXP_ID ? `${BASE}/resultados?expediente_id=${EXP_ID}` : `${BASE}/resultados`;
  await page.goto(hubUrl, { waitUntil: "networkidle0", timeout: 60000 });
  await shot(page, "ir_hub_indicadores");

  if (INF_ID) {
    await page.goto(`${BASE}/resultados/informes/${INF_ID}`, { waitUntil: "networkidle0", timeout: 60000 });
    await shot(page, "ir_informe_narrativo");
  }

  if (EXP_ID) {
    await page.goto(`${BASE}/evaluaciones/${EXP_ID}`, { waitUntil: "networkidle0", timeout: 60000 });
    const tabs = await page.$$("nav.tab-nav button");
    for (const t of tabs) {
      const txt = await page.evaluate((el) => el.textContent, t);
      if (txt && txt.includes("Impacto")) {
        await t.click();
        break;
      }
    }
    await new Promise((r) => setTimeout(r, 800));
    await shot(page, "ir_eval_impacto_link");
  }

  await browser.close();
})().catch((e) => {
  console.error(e);
  process.exit(1);
});

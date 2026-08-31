const puppeteer = require("/tmp/node_modules/puppeteer");
const fs = require("fs");
const path = require("path");

const BASE = process.argv[2] || "http://127.0.0.1:5187";
const INFORME_ID = process.argv[3] || "";
const OUT = "/opt/cursor/artifacts/screenshots";

async function login(page) {
  await page.goto(`${BASE}/login`, { waitUntil: "networkidle0", timeout: 60000 });
  await page.waitForSelector("input");
  const inputs = await page.$$("input");
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
  const browser = await puppeteer.launch({ headless: "new", args: ["--no-sandbox"] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1366, height: 900 });
  await login(page);
  await page.goto(`${BASE}/comunicaciones`, { waitUntil: "networkidle0" });
  await shot(page, "mb11_centro_informacion");
  if (INFORME_ID) {
    await page.goto(`${BASE}/resultados/informes/${INFORME_ID}`, { waitUntil: "networkidle0" });
    await shot(page, "mb11_entrega_informe");
  }
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });

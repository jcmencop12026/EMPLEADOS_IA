/**
 * Branding de certificación visual — logo tenant configurado (sin isotipo EX).
 */

export const CERT_LOGO_DATA_URL =
  "data:image/svg+xml;base64," +
  Buffer.from(
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 280 80" role="img" aria-label="EIAAX Operador Demo">
  <rect width="280" height="80" rx="12" fill="#0c4a6e"/>
  <text x="140" y="48" text-anchor="middle" fill="#ffffff" font-family="Segoe UI, system-ui, sans-serif" font-size="24" font-weight="700">EIAAX Operador</text>
</svg>`,
    "utf-8",
  ).toString("base64");

export const CERT_LOGO_COMPACT_DATA_URL =
  "data:image/svg+xml;base64," +
  Buffer.from(
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 80" role="img" aria-label="EIAAX">
  <rect width="80" height="80" rx="14" fill="#0ea5e9"/>
  <text x="40" y="50" text-anchor="middle" fill="#ffffff" font-family="Segoe UI, system-ui, sans-serif" font-size="20" font-weight="700">EO</text>
</svg>`,
    "utf-8",
  ).toString("base64");

export async function seedCertBranding(page) {
  await page.goto(`${process.env.EIAAX_BASE || "http://127.0.0.1:5180"}/login`, { waitUntil: "domcontentloaded" });
  await page.fill('input[autocomplete="username"]', process.env.EIAAX_USER || "admin");
  await page.fill('input[type="password"]', process.env.EIAAX_PASS || "Admin2026!");
  await page.click("button.login-submit");
  await page.waitForFunction(() => !window.location.pathname.includes("/login"), { timeout: 20000 });
  const ok = await page.evaluate(async ({ logo, compact }) => {
    const token = localStorage.getItem("eaios_token");
    const res = await fetch("/api/admin/config", {
      method: "PUT",
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      body: JSON.stringify({
        enterprise_display_name: "EIAAX Operador Demo",
        enterprise_logo_url: logo,
        enterprise_logo_compact_url: compact,
        enterprise_accent_color: "#0c4a6e",
      }),
    });
    const verify = await fetch("/api/public/login-identity");
    const identity = await verify.json();
    return res.ok && identity.has_configured_logo === true && Boolean(identity.logo_url);
  }, { logo: CERT_LOGO_DATA_URL, compact: CERT_LOGO_COMPACT_DATA_URL });
  if (!ok) throw new Error("No se pudo sembrar branding de certificación");
}

export async function clearCertBranding(page) {
  const ok = await page.evaluate(async () => {
    const token = localStorage.getItem("eaios_token");
    const res = await fetch("/api/admin/config", {
      method: "PUT",
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      body: JSON.stringify({
        enterprise_logo_url: null,
        enterprise_logo_compact_url: null,
      }),
    });
    localStorage.removeItem("eiaax_login_identity_v1");
    const verify = await fetch("/api/public/login-identity");
    const identity = await verify.json();
    return res.ok && identity.has_configured_logo === false;
  });
  if (!ok) throw new Error("No se pudo limpiar branding de certificación");
}

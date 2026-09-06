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

async function putBranding(page, config) {
  const ok = await page.evaluate(async (payload) => {
    const token = localStorage.getItem("eaios_token");
    if (!token) return false;
    const res = await fetch("/api/admin/config", {
      method: "PUT",
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    return res.ok;
  }, config);
  if (!ok) throw new Error("No se pudo actualizar branding de certificación");
}

async function verifyIdentity(page, expectConfigured) {
  return page.evaluate(async (expected) => {
    const verify = await fetch("/api/public/login-identity");
    const identity = await verify.json();
    if (expected) {
      return identity.has_configured_logo === true && Boolean(identity.logo_url);
    }
    return identity.has_configured_logo === false;
  }, expectConfigured);
}

export async function seedCertBranding(page) {
  await putBranding(page, {
    enterprise_display_name: "EIAAX Operador Demo",
    enterprise_logo_url: CERT_LOGO_DATA_URL,
    enterprise_logo_compact_url: CERT_LOGO_COMPACT_DATA_URL,
    enterprise_accent_color: "#0c4a6e",
  });
  const ok = await verifyIdentity(page, true);
  if (!ok) throw new Error("No se pudo sembrar branding de certificación");
}

export async function clearCertBranding(page) {
  await putBranding(page, {
    enterprise_logo_url: null,
    enterprise_logo_compact_url: null,
  });
  await page.evaluate(() => localStorage.removeItem("eiaax_login_identity_v1"));
  const ok = await verifyIdentity(page, false);
  if (!ok) throw new Error("No se pudo limpiar branding de certificación");
}

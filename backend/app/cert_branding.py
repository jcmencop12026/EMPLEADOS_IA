"""Branding de certificación — logo tenant sin isotipo EX (solo seed/demo CI)."""

from __future__ import annotations

import base64

# Logo distintivo para certificación: sin texto "EX", identificable en capturas.
_CERT_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 280 80" role="img" aria-label="EIAAX Operador Demo">
  <rect width="280" height="80" rx="12" fill="#0c4a6e"/>
  <text x="140" y="48" text-anchor="middle" fill="#ffffff" font-family="Segoe UI, system-ui, sans-serif" font-size="24" font-weight="700">EIAAX Operador</text>
</svg>"""

_CERT_COMPACT_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 80" role="img" aria-label="EIAAX">
  <rect width="80" height="80" rx="14" fill="#0ea5e9"/>
  <text x="40" y="50" text-anchor="middle" fill="#ffffff" font-family="Segoe UI, system-ui, sans-serif" font-size="20" font-weight="700">EO</text>
</svg>"""


def cert_tenant_logo_data_url() -> str:
    encoded = base64.b64encode(_CERT_SVG.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def cert_tenant_logo_compact_data_url() -> str:
    encoded = base64.b64encode(_CERT_COMPACT_SVG.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


CERT_BRANDING_CONFIG = {
    "enterprise_display_name": "EIAAX Operador Demo",
    "enterprise_logo_url": cert_tenant_logo_data_url(),
    "enterprise_logo_compact_url": cert_tenant_logo_compact_data_url(),
    "enterprise_accent_color": "#0c4a6e",
}

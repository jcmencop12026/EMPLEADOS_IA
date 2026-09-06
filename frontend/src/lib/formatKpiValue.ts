/** Formatea valores KPI empresariales — evita wrapping patológico en tarjetas. */

export type KpiValueParts = {
  main: string;
  unit?: string;
};

export function splitKpiValueParts(raw: unknown): KpiValueParts {
  const s = String(raw ?? "").trim();
  if (!s || s === "—") return { main: "—" };

  const copYear = s.match(/^(.*?)\s*(COP\s*\/\s*año)\s*$/i);
  if (copYear) return { main: copYear[1].trim(), unit: "COP / año" };

  const copOnly = s.match(/^(.*?)\s*(COP)\s*$/i);
  if (copOnly) return { main: copOnly[1].trim(), unit: "COP" };

  const slashUnit = s.match(/^(.*?)\s*\/\s*(año|mes|periodo)\s*$/i);
  if (slashUnit) return { main: slashUnit[1].trim(), unit: `/${slashUnit[2]}` };

  if (s.length > 18 && s.includes(" ")) {
    const parts = s.split(/\s+/);
    if (parts.length >= 2) {
      return { main: parts.slice(0, -1).join(" "), unit: parts[parts.length - 1] };
    }
  }

  return { main: s };
}

export function formatValorPotencialKpi(raw: unknown): KpiValueParts {
  if (raw === null || raw === undefined) return { main: "—" };
  if (typeof raw === "number") {
    return {
      main: new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 }).format(raw),
      unit: "COP / año",
    };
  }

  const s = String(raw).trim();
  if (!s || s === "—") return { main: "—" };

  const moneyInDemo = s.match(/\$\s*[\d.,]+[KMB]?(?:\s*COP)?(?:\s*\/\s*año)?/i);
  if (moneyInDemo) {
    const main = moneyInDemo[0].replace(/\s*COP.*$/i, "").trim();
    return { main, unit: "COP / año" };
  }

  const parts = splitKpiValueParts(s);
  if (!parts.unit && /^\$|^\d/.test(parts.main)) {
    return { ...parts, unit: "COP / año" };
  }
  return parts;
}

import { useCallback, useEffect, useState } from "react";
import type { FinOpsBudget, FinOpsConsumption, FinOpsDashboard, FinOpsRate } from "../api";
import {
  createFinOpsBudget,
  createFinOpsRate,
  fetchFinOpsBudgets,
  fetchFinOpsConsumptions,
  fetchFinOpsDashboard,
  fetchFinOpsRates,
} from "../api";
import { getCachedUser } from "../auth/session";

type Tab = "resumen" | "consumos" | "presupuestos" | "tarifas";

export function CostosValorPage() {
  const user = getCachedUser();
  const canBudget = user?.permissions?.includes("finops.budget");
  const canRates = user?.permissions?.includes("finops.rates");
  const [tab, setTab] = useState<Tab>("resumen");
  const [summary, setSummary] = useState<FinOpsDashboard | null>(null);
  const [consumptions, setConsumptions] = useState<FinOpsConsumption[]>([]);
  const [budgets, setBudgets] = useState<FinOpsBudget[]>([]);
  const [rates, setRates] = useState<FinOpsRate[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState({
    provider: "",
    model_name: "",
    opportunity_id: "",
    category: "",
  });

  const load = useCallback(() => {
    setError(null);
    const consumptionParams = {
      provider: filters.provider || undefined,
      model_name: filters.model_name || undefined,
      opportunity_id: filters.opportunity_id || undefined,
      category: filters.category || undefined,
    };
    const tasks = [
      fetchFinOpsDashboard(),
      fetchFinOpsConsumptions(consumptionParams),
    ];
    if (canBudget) tasks.push(fetchFinOpsBudgets());
    if (canRates) tasks.push(fetchFinOpsRates());
    Promise.all(tasks)
      .then((results) => {
        setSummary(results[0] as FinOpsDashboard);
        setConsumptions(results[1] as FinOpsConsumption[]);
        let idx = 2;
        if (canBudget) {
          setBudgets(results[idx] as FinOpsBudget[]);
          idx += 1;
        }
        if (canRates) setRates(results[idx] as FinOpsRate[]);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Error al cargar FinOps"));
  }, [canBudget, canRates, filters]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleCreateBudget(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const now = new Date();
    const end = new Date(now);
    end.setMonth(end.getMonth() + 1);
    await createFinOpsBudget({
      scope_type: String(form.get("scope_type") || "empresa"),
      name: String(form.get("name") || "Presupuesto IA"),
      period_start: now.toISOString(),
      period_end: end.toISOString(),
      amount_limit: String(form.get("amount_limit") || "100"),
      currency: String(form.get("currency") || "USD"),
      policy: String(form.get("policy") || "Solo informar"),
      alert_threshold_pct: Number(form.get("alert_threshold_pct") || 90),
    });
    load();
  }

  async function handleCreateRate(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    await createFinOpsRate({
      provider: String(form.get("provider") || "openai"),
      model_service: String(form.get("model_service") || "gpt-4o-mini"),
      category: "Modelo IA",
      price_input: String(form.get("price_input") || "0.00001"),
      price_output: String(form.get("price_output") || "0.00002"),
      currency: "USD",
      active: true,
    });
    load();
  }

  return (
    <div className="ops-page">
      <header className="page-header">
        <h1>Costos y valor</h1>
        <p className="muted">Consumo IA, presupuestos, tarifas y trazabilidad por oportunidad</p>
      </header>
      {error && <p className="error">{error}</p>}

      <div className="tab-bar">
        {(["resumen", "consumos", "presupuestos", "tarifas"] as Tab[]).map((t) => (
          <button
            key={t}
            type="button"
            className={tab === t ? "tab active" : "tab"}
            onClick={() => setTab(t)}
          >
            {t === "resumen" && "Resumen"}
            {t === "consumos" && "Consumos"}
            {t === "presupuestos" && "Presupuestos"}
            {t === "tarifas" && "Tarifas"}
          </button>
        ))}
      </div>

      {tab === "resumen" && summary && (
        <div className="panel metrics-grid">
          <div className="metric-card">
            <span className="metric-label">Costo del período</span>
            <strong>{summary.total_cost_label}</strong>
          </div>
          <div className="metric-card">
            <span className="metric-label">Valor generado</span>
            <strong>{summary.total_value_label}</strong>
          </div>
          <div className="metric-card">
            <span className="metric-label">Beneficio neto</span>
            <strong>{summary.net_benefit ?? "—"}</strong>
          </div>
          <div className="metric-card">
            <span className="metric-label">Retorno de inversión</span>
            <strong>{summary.roi_label}</strong>
          </div>
          <div className="metric-card">
            <span className="metric-label">Ejecuciones</span>
            <strong>{summary.execution_count}</strong>
          </div>
        </div>
      )}

      {tab === "consumos" && (
        <>
          <div className="panel filters-row">
            <input
              placeholder="Proveedor"
              value={filters.provider}
              onChange={(e) => setFilters({ ...filters, provider: e.target.value })}
            />
            <input
              placeholder="Modelo"
              value={filters.model_name}
              onChange={(e) => setFilters({ ...filters, model_name: e.target.value })}
            />
            <input
              placeholder="ID oportunidad"
              value={filters.opportunity_id}
              onChange={(e) => setFilters({ ...filters, opportunity_id: e.target.value })}
            />
            <input
              placeholder="Categoría"
              value={filters.category}
              onChange={(e) => setFilters({ ...filters, category: e.target.value })}
            />
            <button type="button" className="btn-secondary" onClick={load}>
              Filtrar
            </button>
          </div>
          <div className="panel table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Categoría</th>
                  <th>Proveedor</th>
                  <th>Modelo</th>
                  <th>Oportunidad</th>
                  <th>Tokens</th>
                  <th>Costo</th>
                  <th>Fecha</th>
                </tr>
              </thead>
              <tbody>
                {consumptions.length === 0 && (
                  <tr>
                    <td colSpan={7} className="muted">
                      Sin consumos registrados.
                    </td>
                  </tr>
                )}
                {consumptions.map((row) => (
                  <tr key={row.id}>
                    <td>{row.category || "—"}</td>
                    <td>{row.provider || "—"}</td>
                    <td>{row.model_name || "—"}</td>
                    <td className="mono">{row.opportunity_id?.slice(0, 8) || "—"}</td>
                    <td>
                      {(row.tokens_in ?? 0) + (row.tokens_out ?? 0) || "—"}
                    </td>
                    <td>{row.cost_label}</td>
                    <td className="mono">{row.created_at?.slice(0, 19)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {tab === "presupuestos" && (
        <>
          {!canBudget && <p className="muted">Sin permiso para gestionar presupuestos.</p>}
          {canBudget && (
            <form className="panel form-grid" onSubmit={handleCreateBudget}>
              <h2>Nuevo presupuesto IA</h2>
              <label>
                Nombre
                <input name="name" placeholder="Presupuesto mensual IA" />
              </label>
              <label>
                Límite
                <input name="amount_limit" type="number" step="0.01" defaultValue="100" />
              </label>
              <label>
                Política
                <select name="policy" defaultValue="Solo informar">
                  <option value="Solo informar">Solo informar (alerta)</option>
                  <option value="Requiere aprobación">Requiere aprobación</option>
                  <option value="Bloquear">Bloquear ejecución</option>
                </select>
              </label>
              <label>
                Umbral alerta (%)
                <input name="alert_threshold_pct" type="number" min={50} max={100} defaultValue={90} />
              </label>
              <input type="hidden" name="scope_type" value="empresa" />
              <input type="hidden" name="currency" value="USD" />
              <button type="submit" className="btn-primary">
                Crear presupuesto
              </button>
            </form>
          )}
          <div className="panel table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Nombre</th>
                  <th>Consumido</th>
                  <th>Disponible</th>
                  <th>Estado</th>
                  <th>Política</th>
                  <th>Bloquea</th>
                </tr>
              </thead>
              <tbody>
                {budgets.map((b) => (
                  <tr key={b.id}>
                    <td>{b.name || b.scope_type}</td>
                    <td>
                      {b.spent} {b.currency}
                    </td>
                    <td>
                      {b.balance} {b.currency}
                    </td>
                    <td>{b.state}</td>
                    <td>{b.policy}</td>
                    <td>{b.blocks_execution ? "Sí" : "No"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {tab === "tarifas" && (
        <>
          {!canRates && <p className="muted">Sin permiso para gestionar tarifas.</p>}
          {canRates && (
            <form className="panel form-grid" onSubmit={handleCreateRate}>
              <h2>Nueva tarifa</h2>
              <label>
                Proveedor
                <input name="provider" defaultValue="openai" />
              </label>
              <label>
                Modelo
                <input name="model_service" defaultValue="gpt-4o-mini" />
              </label>
              <label>
                Precio entrada (por token)
                <input name="price_input" defaultValue="0.00001" />
              </label>
              <label>
                Precio salida (por token)
                <input name="price_output" defaultValue="0.00002" />
              </label>
              <button type="submit" className="btn-primary">
                Crear tarifa
              </button>
            </form>
          )}
          <div className="panel table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Proveedor</th>
                  <th>Modelo</th>
                  <th>Entrada</th>
                  <th>Salida</th>
                  <th>Activa</th>
                </tr>
              </thead>
              <tbody>
                {rates.map((r) => (
                  <tr key={r.id}>
                    <td>{r.provider || "—"}</td>
                    <td>{r.model_service || "—"}</td>
                    <td>{r.price_input ?? "—"}</td>
                    <td>{r.price_output ?? "—"}</td>
                    <td>{r.active ? "Sí" : "No"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}

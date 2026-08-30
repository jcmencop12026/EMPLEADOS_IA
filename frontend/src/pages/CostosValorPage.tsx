import { useCallback, useEffect, useState } from "react";
import type {
  FinOpsBudget,
  FinOpsConsumption,
  FinOpsDashboard,
  FinOpsRate,
  PlannerPresupuesto,
  PlannerResumen,
  PlannerSimulation,
} from "../api";
import {
  comparePlannerProviders,
  createFinOpsBudget,
  createFinOpsRate,
  fetchFinOpsBudgets,
  fetchFinOpsConsumptions,
  fetchFinOpsDashboard,
  fetchFinOpsRates,
  fetchPlannerCapacidad,
  fetchPlannerMargen,
  fetchPlannerPresupuesto,
  fetchPlannerResumen,
  simulatePlannerConsumption,
} from "../api";
import { getCachedUser } from "../auth/session";

type Tab = "resumen" | "consumos" | "capacidad" | "simulador" | "presupuesto" | "comparacion" | "presupuestos" | "tarifas";

export function CostosValorPage() {
  const user = getCachedUser();
  const canBudget = user?.permissions?.includes("finops.budget");
  const canRates = user?.permissions?.includes("finops.rates");
  const canSimulate = user?.permissions?.includes("finops.planner.simulate");
  const canMargin = user?.permissions?.includes("finops.margin.view");
  const [tab, setTab] = useState<Tab>("resumen");
  const [summary, setSummary] = useState<FinOpsDashboard | null>(null);
  const [planner, setPlanner] = useState<PlannerResumen | null>(null);
  const [presupuesto, setPresupuesto] = useState<PlannerPresupuesto | null>(null);
  const [capacidad, setCapacidad] = useState<Record<string, unknown> | null>(null);
  const [simResult, setSimResult] = useState<PlannerSimulation | null>(null);
  const [compareRows, setCompareRows] = useState<Array<Record<string, unknown>>>([]);
  const [margin, setMargin] = useState<Record<string, unknown> | null>(null);
  const [consumptions, setConsumptions] = useState<FinOpsConsumption[]>([]);
  const [budgets, setBudgets] = useState<FinOpsBudget[]>([]);
  const [rates, setRates] = useState<FinOpsRate[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [simParams, setSimParams] = useState({ employees: 25, execDay: 20, days: 30 });
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
    const tasks: Promise<unknown>[] = [
      fetchFinOpsDashboard(),
      fetchFinOpsConsumptions(consumptionParams),
      fetchPlannerResumen(),
      fetchPlannerPresupuesto(),
      fetchPlannerCapacidad(),
    ];
    if (canBudget) tasks.push(fetchFinOpsBudgets());
    if (canRates) tasks.push(fetchFinOpsRates());
    if (canMargin) tasks.push(fetchPlannerMargen());
    Promise.all(tasks)
      .then((results) => {
        setSummary(results[0] as FinOpsDashboard);
        setConsumptions(results[1] as FinOpsConsumption[]);
        setPlanner(results[2] as PlannerResumen);
        setPresupuesto(results[3] as PlannerPresupuesto);
        setCapacidad(results[4] as Record<string, unknown>);
        let idx = 5;
        if (canBudget) {
          setBudgets(results[idx] as FinOpsBudget[]);
          idx += 1;
        }
        if (canRates) {
          setRates(results[idx] as FinOpsRate[]);
          idx += 1;
        }
        if (canMargin) {
          setMargin(results[idx] as Record<string, unknown>);
        }
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Error al cargar FinOps"));
  }, [canBudget, canRates, canMargin, filters]);

  useEffect(() => {
    load();
  }, [load]);

  async function runSimulation() {
    if (!canSimulate) return;
    setError(null);
    try {
      const result = await simulatePlannerConsumption({
        active_employees: simParams.employees,
        executions_per_day: simParams.execDay,
        days: simParams.days,
      });
      setSimResult(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error en simulación");
    }
  }

  async function runCompare() {
    setError(null);
    try {
      const rows = await comparePlannerProviders({
        tokens_in: 1500,
        tokens_out: 800,
        scenarios: [
          { provider: "openai", model: "gpt-4o-mini" },
          { provider: "openai", model: "gpt-4o" },
          { provider: "anthropic", model: "claude-3-5-sonnet" },
        ],
      });
      setCompareRows(rows);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error en comparación");
    }
  }

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

  const tabs: { id: Tab; label: string }[] = [
    { id: "resumen", label: "Resumen" },
    { id: "consumos", label: "Consumos" },
    { id: "capacidad", label: "Capacidad" },
    { id: "simulador", label: "Simulador" },
    { id: "presupuesto", label: "Presupuesto" },
    { id: "comparacion", label: "Comparación" },
    { id: "presupuestos", label: "Presupuestos" },
    { id: "tarifas", label: "Tarifas" },
  ];

  return (
    <div className="ops-page">
      <header className="page-header">
        <h1>Costos y valor</h1>
        <p className="muted">Consumo IA, capacidad, simulación y presupuestos (FinOps + planificador MB-07)</p>
      </header>
      {error && <p className="error">{error}</p>}

      <div className="tab-bar">
        {tabs.map((t) => (
          <button
            key={t.id}
            type="button"
            className={tab === t.id ? "tab active" : "tab"}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "resumen" && (summary || planner) && (
        <div className="panel metrics-grid">
          <div className="metric-card">
            <span className="metric-label">Costo real (período)</span>
            <strong>{summary?.total_cost_label ?? "—"}</strong>
          </div>
          <div className="metric-card">
            <span className="metric-label">Consumo real org.</span>
            <strong>{planner ? `${planner.consumo_real.toFixed(2)} ${planner.currency}` : "—"}</strong>
          </div>
          <div className="metric-card">
            <span className="metric-label">Proyectado mensual</span>
            <strong>{planner ? `${planner.consumo_proyectado_mes.toFixed(2)} ${planner.currency}` : "—"}</strong>
          </div>
          <div className="metric-card">
            <span className="metric-label">Directo / Transversal / Plataforma</span>
            <strong>
              {planner
                ? `${planner.real_by_class.DIRECTO?.cost_total ?? 0} / ${planner.real_by_class.TRANSVERSAL_ATRIBUIBLE?.cost_total ?? 0} / ${planner.real_by_class.PLATAFORMA?.cost_total ?? 0}`
                : "—"}
            </strong>
          </div>
          <div className="metric-card">
            <span className="metric-label">Valor generado</span>
            <strong>{summary?.total_value_label ?? "—"}</strong>
          </div>
          {canMargin && margin?.available && (
            <div className="metric-card">
              <span className="metric-label">Margen bruto est.</span>
              <strong>{String(margin.gross_margin)} {String(margin.currency ?? "")}</strong>
            </div>
          )}
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
            <table className="data-table compact">
              <thead>
                <tr>
                  <th>Categoría</th>
                  <th>Proveedor</th>
                  <th>Modelo</th>
                  <th>Tokens</th>
                  <th>Costo</th>
                  <th>Fecha</th>
                </tr>
              </thead>
              <tbody>
                {consumptions.length === 0 && (
                  <tr>
                    <td colSpan={6} className="muted">Sin consumos registrados.</td>
                  </tr>
                )}
                {consumptions.map((row) => (
                  <tr key={row.id}>
                    <td>{row.category || "—"}</td>
                    <td>{row.provider || "—"}</td>
                    <td>{row.model_name || "—"}</td>
                    <td>{(row.tokens_in ?? 0) + (row.tokens_out ?? 0) || "—"}</td>
                    <td>{row.cost_label}</td>
                    <td className="mono">{row.created_at?.slice(0, 19)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {tab === "capacidad" && capacidad && (
        <div className="panel metrics-grid">
          <div className="metric-card">
            <span className="metric-label">Concurrencia máxima</span>
            <strong>{String(capacidad.max_concurrency ?? "—")}</strong>
          </div>
          <div className="metric-card">
            <span className="metric-label">Ejecuciones / día</span>
            <strong>{String(capacidad.executions_per_day ?? "—")}</strong>
          </div>
          <div className="metric-card">
            <span className="metric-label">Ejecuciones / hora</span>
            <strong>{String(capacidad.executions_per_hour ?? "—")}</strong>
          </div>
          <div className="metric-card">
            <span className="metric-label">Capacidad comprometida</span>
            <strong>{String(capacidad.capacity_committed_daily ?? "—")}</strong>
          </div>
          <div className="metric-card">
            <span className="metric-label">Capacidad disponible</span>
            <strong>{String(capacidad.capacity_available ?? "—")}</strong>
          </div>
        </div>
      )}

      {tab === "simulador" && (
        <div className="panel form-grid">
          {!canSimulate && <p className="muted">Sin permiso para simular consumo.</p>}
          {canSimulate && (
            <>
              <h2>¿Qué pasa si…?</h2>
              <label>
                Empleados IA activos
                <input
                  type="number"
                  value={simParams.employees}
                  onChange={(e) => setSimParams({ ...simParams, employees: Number(e.target.value) })}
                />
              </label>
              <label>
                Ejecuciones / día / empleado
                <input
                  type="number"
                  value={simParams.execDay}
                  onChange={(e) => setSimParams({ ...simParams, execDay: Number(e.target.value) })}
                />
              </label>
              <label>
                Días
                <input
                  type="number"
                  value={simParams.days}
                  onChange={(e) => setSimParams({ ...simParams, days: Number(e.target.value) })}
                />
              </label>
              <button type="button" className="btn-primary" onClick={runSimulation}>
                Simular
              </button>
            </>
          )}
          {simResult && (
            <div className="metrics-grid">
              <div className="metric-card">
                <span className="metric-label">Ejecuciones mensuales</span>
                <strong>{String(simResult.directo.executions_monthly ?? "—")}</strong>
              </div>
              <div className="metric-card">
                <span className="metric-label">Costo total proyectado</span>
                <strong>{simResult.cost_total.toFixed(2)}</strong>
              </div>
              <div className="metric-card">
                <span className="metric-label">Sobreconsumo</span>
                <strong>{simResult.sobreconsumo.toFixed(2)}</strong>
              </div>
              <div className="metric-card">
                <span className="metric-label">Riesgo presupuesto</span>
                <strong>{String(simResult.budget?.risk ?? "—")}</strong>
              </div>
              {simResult.demo_notice && <p className="muted">{simResult.demo_notice}</p>}
            </div>
          )}
        </div>
      )}

      {tab === "presupuesto" && presupuesto && (
        <div className="panel metrics-grid">
          <div className="metric-card">
            <span className="metric-label">Presupuesto IA</span>
            <strong>{presupuesto.presupuesto_ia} {presupuesto.currency}</strong>
          </div>
          <div className="metric-card">
            <span className="metric-label">Consumo incluido</span>
            <strong>{presupuesto.consumo_incluido} {presupuesto.currency}</strong>
          </div>
          <div className="metric-card">
            <span className="metric-label">Consumo real</span>
            <strong>{presupuesto.consumo_real} {presupuesto.currency}</strong>
          </div>
          <div className="metric-card">
            <span className="metric-label">Proyección cierre mes</span>
            <strong>{presupuesto.proyeccion_cierre_mes} {presupuesto.currency}</strong>
          </div>
          <div className="metric-card">
            <span className="metric-label">% utilizado</span>
            <strong>{presupuesto.porcentaje_utilizado ?? "—"}</strong>
          </div>
          <div className="metric-card">
            <span className="metric-label">Sobreconsumo</span>
            <strong>{presupuesto.sobreconsumo} {presupuesto.currency}</strong>
          </div>
        </div>
      )}

      {tab === "comparacion" && (
        <div className="panel">
          <button type="button" className="btn-secondary" onClick={runCompare}>
            Comparar proveedores (catálogo configurado)
          </button>
          <table className="data-table compact">
            <thead>
              <tr>
                <th>Proveedor</th>
                <th>Modelo</th>
                <th>Costo est.</th>
                <th>Moneda</th>
                <th>Catálogo</th>
              </tr>
            </thead>
            <tbody>
              {compareRows.map((row, i) => (
                <tr key={i}>
                  <td>{String(row.provider ?? "—")}</td>
                  <td>{String(row.model ?? "—")}</td>
                  <td>{String(row.cost_estimated ?? "—")}</td>
                  <td>{String(row.currency ?? "—")}</td>
                  <td>{row.rate_configured ? "Sí" : "No"}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="muted">Comparación basada en tarifas configuradas — no implica recomendación automática.</p>
        </div>
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
              <button type="submit" className="btn-primary">Crear presupuesto</button>
            </form>
          )}
          <div className="panel table-wrap">
            <table className="data-table compact">
              <thead>
                <tr>
                  <th>Nombre</th>
                  <th>Consumido</th>
                  <th>Disponible</th>
                  <th>Estado</th>
                </tr>
              </thead>
              <tbody>
                {budgets.map((b) => (
                  <tr key={b.id}>
                    <td>{b.name || b.scope_type}</td>
                    <td>{b.spent} {b.currency}</td>
                    <td>{b.balance} {b.currency}</td>
                    <td>{b.state}</td>
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
              <button type="submit" className="btn-primary">Crear tarifa</button>
            </form>
          )}
          <div className="panel table-wrap">
            <table className="data-table compact">
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

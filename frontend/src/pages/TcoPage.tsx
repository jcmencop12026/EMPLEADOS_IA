import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  calcularTco,
  compararProveedoresTco,
  createTcoCosto,
  createTcoProveedor,
  fetchTcoAlianzas,
  fetchTcoCostos,
  fetchTcoProveedores,
  fetchTcoRentabilidad,
  fetchTcoTablero,
  simularMakeOrBuy,
  simularTco,
  type TcoProveedorItem,
  type TcoTablero,
} from "../api";
import { usePermissions } from "../hooks/usePermissions";

type Tab = "tablero" | "proveedores" | "rentabilidad" | "simulador" | "alianzas";

export function TcoPage() {
  const { has } = usePermissions();
  const [tab, setTab] = useState<Tab>("tablero");
  const [tablero, setTablero] = useState<TcoTablero | null>(null);
  const [proveedores, setProveedores] = useState<TcoProveedorItem[]>([]);
  const [costos, setCostos] = useState<Array<Record<string, unknown>>>([]);
  const [alianzas, setAlianzas] = useState<Array<Record<string, unknown>>>([]);
  const [rentabilidad, setRentabilidad] = useState<Record<string, unknown> | null>(null);
  const [simResult, setSimResult] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [nuevoCosto, setNuevoCosto] = useState({ nombre: "", monto: "1000000", categoria_code: "INFRAESTRUCTURA" });
  const [nuevoProv, setNuevoProv] = useState({ nombre: "", tipo: "PROVEEDOR_IA" });
  const [makeOrBuy, setMakeOrBuy] = useState({ costo_interno: "50000000", costo_tercero: "35000000" });

  useEffect(() => {
    const tasks: Promise<unknown>[] = [fetchTcoTablero().then(setTablero)];
    if (has("proveedores.view")) tasks.push(fetchTcoProveedores().then(setProveedores));
    if (has("tco.view")) tasks.push(fetchTcoCostos().then(setCostos));
    if (has("alianzas.view")) tasks.push(fetchTcoAlianzas().then(setAlianzas));
    Promise.all(tasks)
      .catch((e) => setError(e instanceof Error ? e.message : "Error"))
      .finally(() => setLoading(false));
  }, [has]);

  async function onCalcularTco() {
    const result = await calcularTco({ guardar_snapshot: true, ingreso: 15000000 });
    setTablero({ ...tablero!, tco_total: result.total, desglose: result.desglose, margen_pct: result.margen_pct });
  }

  async function onAddCosto(e: FormEvent) {
    e.preventDefault();
    await createTcoCosto({
      nombre: nuevoCosto.nombre,
      monto: Number(nuevoCosto.monto),
      categoria_code: nuevoCosto.categoria_code,
      tipo_costo: "FIJO",
      naturaleza: "ESTIMADO",
    });
    setCostos(await fetchTcoCostos());
    setTablero(await fetchTcoTablero());
  }

  async function onAddProveedor(e: FormEvent) {
    e.preventDefault();
    await createTcoProveedor({ nombre: nuevoProv.nombre, tipo: nuevoProv.tipo });
    setProveedores(await fetchTcoProveedores());
  }

  async function onRentabilidad() {
    setRentabilidad(await fetchTcoRentabilidad({ ingreso_estimado: 15000000 }));
  }

  async function onSimularConsumo() {
    setSimResult(await simularTco({ tipo: "AUMENTO_CONSUMO", parametros: { factor: 1.5 } }));
  }

  async function onMakeOrBuy(e: FormEvent) {
    e.preventDefault();
    setSimResult(
      await simularMakeOrBuy({
        costo_interno: Number(makeOrBuy.costo_interno),
        costo_tercero: Number(makeOrBuy.costo_tercero),
      }),
    );
  }

  async function onComparar() {
    if (proveedores.length < 2) return;
    setSimResult({
      comparacion: await compararProveedoresTco({
        proveedor_ids: proveedores.slice(0, 2).map((p) => p.id),
        unidades: 2_000_000,
      }),
    });
  }

  const tabs: { id: Tab; label: string; perm: string }[] = [
    { id: "tablero", label: "Costo total", perm: "tco.view" },
    { id: "proveedores", label: "Proveedores y aliados", perm: "proveedores.view" },
    { id: "rentabilidad", label: "Rentabilidad", perm: "tco.view" },
    { id: "simulador", label: "Simulador", perm: "tco.simulate" },
    { id: "alianzas", label: "Alianzas", perm: "alianzas.view" },
  ];

  return (
    <div className="ops-page">
      <header className="ops-header">
        <h1>TCO y ecosistema de aliados</h1>
        <p>Costo total de propiedad, proveedores, rentabilidad y simulaciones.</p>
      </header>
      {error && <p className="error-text">{error}</p>}
      <nav className="tab-nav">
        {tabs.filter((t) => has(t.perm)).map((t) => (
          <button key={t.id} type="button" className={tab === t.id ? "active" : ""} onClick={() => setTab(t.id)}>
            {t.label}
          </button>
        ))}
      </nav>
      {loading ? (
        <p>Cargando…</p>
      ) : (
        <>
          {tab === "tablero" && tablero && (
            <section className="panel">
              <h2>Tablero TCO</h2>
              <div className="metric-grid">
                <div className="metric-card">
                  <span className="metric-label">TCO estimado</span>
                  <strong>{tablero.tco_total?.toLocaleString("es-CO")}</strong>
                </div>
                {tablero.margen_pct != null && (
                  <div className="metric-card">
                    <span className="metric-label">Margen</span>
                    <strong>{tablero.margen_pct.toFixed(1)}%</strong>
                  </div>
                )}
                {tablero.desviacion && (
                  <div className="metric-card">
                    <span className="metric-label">Desviación est. vs real</span>
                    <strong>{tablero.desviacion.desviacion_pct?.toFixed(1)}%</strong>
                  </div>
                )}
              </div>
              {tablero.desglose && (
                <ul>
                  {Object.entries(tablero.desglose).map(([k, v]) => (
                    <li key={k}>
                      {k}: {(v as number).toLocaleString("es-CO")}
                    </li>
                  ))}
                </ul>
              )}
              {tablero.alertas && tablero.alertas.length > 0 && (
                <div className="alert-box">
                  <h3>Alertas económicas</h3>
                  {tablero.alertas.map((a, i) => (
                    <p key={i}>
                      [{a.severidad}] {a.mensaje}
                    </p>
                  ))}
                </div>
              )}
              {has("tco.manage") && (
                <form onSubmit={onAddCosto} className="inline-form">
                  <input placeholder="Nombre costo" value={nuevoCosto.nombre} onChange={(e) => setNuevoCosto({ ...nuevoCosto, nombre: e.target.value })} required />
                  <input placeholder="Monto" value={nuevoCosto.monto} onChange={(e) => setNuevoCosto({ ...nuevoCosto, monto: e.target.value })} />
                  <button type="submit">Agregar costo</button>
                </form>
              )}
              {has("tco.view") && (
                <button type="button" onClick={onCalcularTco}>
                  Recalcular TCO
                </button>
              )}
              <h3>Costos registrados ({costos.length})</h3>
              <ul>
                {costos.slice(0, 10).map((c) => (
                  <li key={String(c.id)}>
                    {String(c.nombre)} — {(c.monto as number).toLocaleString("es-CO")} ({String(c.naturaleza)})
                  </li>
                ))}
              </ul>
            </section>
          )}
          {tab === "proveedores" && (
            <section className="panel">
              <h2>Proveedores y aliados</h2>
              {has("proveedores.manage") && (
                <form onSubmit={onAddProveedor} className="inline-form">
                  <input placeholder="Nombre" value={nuevoProv.nombre} onChange={(e) => setNuevoProv({ ...nuevoProv, nombre: e.target.value })} required />
                  <select value={nuevoProv.tipo} onChange={(e) => setNuevoProv({ ...nuevoProv, tipo: e.target.value })}>
                    <option value="PROVEEDOR_IA">Proveedor IA</option>
                    <option value="PROVEEDOR_INFRAESTRUCTURA">Infraestructura</option>
                    <option value="ALIADO_TECNOLOGICO">Aliado tecnológico</option>
                  </select>
                  <button type="submit">Agregar</button>
                </form>
              )}
              <ul>
                {proveedores.map((p) => (
                  <li key={p.id}>
                    {p.nombre} — {p.tipo} — Riesgo: {p.riesgo_nivel}
                  </li>
                ))}
              </ul>
              <Link to="/costos-valor">Ver consumo FinOps →</Link>
            </section>
          )}
          {tab === "rentabilidad" && (
            <section className="panel">
              <h2>Rentabilidad por cliente</h2>
              <button type="button" onClick={onRentabilidad}>
                Calcular rentabilidad
              </button>
              {rentabilidad && (
                <pre>{JSON.stringify(rentabilidad, null, 2)}</pre>
              )}
            </section>
          )}
          {tab === "simulador" && (
            <section className="panel">
              <h2>Simulador de costos</h2>
              <p>La simulación no modifica valores definitivos.</p>
              <button type="button" onClick={onSimularConsumo}>
                Simular aumento de consumo (+50%)
              </button>
              <button type="button" onClick={onComparar} disabled={proveedores.length < 2}>
                Comparar proveedores
              </button>
              <form onSubmit={onMakeOrBuy} className="inline-form">
                <h3>Make or Buy</h3>
                <input value={makeOrBuy.costo_interno} onChange={(e) => setMakeOrBuy({ ...makeOrBuy, costo_interno: e.target.value })} />
                <input value={makeOrBuy.costo_tercero} onChange={(e) => setMakeOrBuy({ ...makeOrBuy, costo_tercero: e.target.value })} />
                <button type="submit">Comparar hacer vs contratar</button>
              </form>
              {simResult && <pre>{JSON.stringify(simResult, null, 2)}</pre>}
            </section>
          )}
          {tab === "alianzas" && (
            <section className="panel">
              <h2>Alianzas estratégicas</h2>
              <ul>
                {alianzas.map((a) => (
                  <li key={String(a.id)}>
                    {String(a.nombre)} — {String(a.tipo)} — {String(a.estado)}
                  </li>
                ))}
              </ul>
              {alianzas.length === 0 && <p>Sin alianzas registradas.</p>}
            </section>
          )}
        </>
      )}
    </div>
  );
}

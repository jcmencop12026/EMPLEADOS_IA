import { FormEvent, useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  createEmployeeFromRequerimiento,
  diagnosticarTransformacion,
  fetchDossier,
  fetchRecorridoTransformacion,
  fetchRequerimientosEmpleadoIA,
  registrarNecesidadTransformacion,
  type TransformacionDossier,
  type TransformacionRecorrido,
} from "../api";
import { usePermissions } from "../hooks/usePermissions";

type Paso = "inicio" | "necesidad" | "informacion" | "diagnostico" | "transformacion" | "accion";

const PASO_LABELS: Record<Paso, string> = {
  inicio: "Inicio",
  necesidad: "Necesidad",
  informacion: "Qué sabemos / qué falta",
  diagnostico: "Qué encontramos",
  transformacion: "Qué recomendamos",
  accion: "Qué hacer ahora",
};

export function ArquitectoTransformacionPage() {
  const { has } = usePermissions();
  const [paso, setPaso] = useState<Paso>("inicio");
  const [dossier, setDossier] = useState<TransformacionDossier | null>(null);
  const [recorrido, setRecorrido] = useState<TransformacionRecorrido | null>(null);
  const [resultado, setResultado] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [requerimientos, setRequerimientos] = useState<Array<Record<string, unknown>>>([]);
  const [form, setForm] = useState({
    titulo: "",
    necesidad: "",
    objetivo: "",
    area_proceso: "",
    nivel: "PRELIMINAR",
  });

  useEffect(() => {
    if (paso === "transformacion" || paso === "accion") {
      fetchRequerimientosEmpleadoIA().then((r) => setRequerimientos(r.items)).catch(() => undefined);
    }
  }, [paso]);

  async function onCrearEmpleadoDesdeReq(reqId: string) {
    try {
      const r = await createEmployeeFromRequerimiento(reqId);
      const empId = (r.employee as { id?: string })?.id;
      if (empId) window.location.href = `/empleados/${empId}/editar`;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al crear empleado");
    }
  }

  const load = useCallback(() => {
    setLoading(true);
    Promise.all([fetchDossier().catch(() => null), fetchRecorridoTransformacion().catch(() => null)])
      .then(([d, r]) => {
        setDossier(d);
        setRecorrido(r);
        setError(null);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Error"))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { load(); }, [load]);

  async function onRegistrar(e: FormEvent) {
    e.preventDefault();
    try {
      const r = await registrarNecesidadTransformacion(form);
      setResultado(r);
      setPaso("informacion");
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al registrar");
    }
  }

  async function onDiagnosticar() {
    const eid = dossier?.expediente_activo_id || (resultado?.expediente as { id?: string })?.id;
    if (!eid) {
      setError("No hay expediente activo");
      return;
    }
    try {
      const r = await diagnosticarTransformacion(eid);
      setResultado(r);
      setPaso("transformacion");
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al diagnosticar");
    }
  }

  const expedienteId = dossier?.expediente_activo_id || (resultado?.expediente as { id?: string })?.id;

  return (
    <div className="ops-page">
      <header className="page-header">
        <h1>Arquitecto de Transformación</h1>
        <p className="muted">Diagnóstico 360 adaptativo — comprender, diagnosticar y proponer transformación empresarial</p>
      </header>

      {error && <p className="error">{error}</p>}

      <nav className="tab-nav compact-tabs">
        {(Object.keys(PASO_LABELS) as Paso[]).map((p) => (
          <button
            key={p}
            type="button"
            className={paso === p ? "tab active" : "tab"}
            onClick={() => setPaso(p)}
          >
            {PASO_LABELS[p]}
          </button>
        ))}
      </nav>

      {loading && paso === "inicio" && <p className="muted">Cargando dossier…</p>}

      {paso === "inicio" && dossier && (
        <div className="panel compact-panel">
          <h2>Dossier empresarial</h2>
          <dl className="detail-grid">
            <dt>Etapa</dt><dd>{dossier.etapa_actual}</dd>
            <dt>Confianza</dt><dd>{dossier.confianza_global}</dd>
            <dt>Completitud</dt><dd>{dossier.porcentaje_completitud}%</dd>
            <dt>Expediente activo</dt>
            <dd>
              {expedienteId ? (
                <Link to={`/evaluaciones/${expedienteId}`}>{dossier.expediente_activo?.codigo || expedienteId}</Link>
              ) : "—"}
            </dd>
          </dl>
          {recorrido?.pasos && (
            <ul className="recorrido-list">
              {recorrido.pasos.map((s) => (
                <li key={s.id} className={s.completo ? "completo" : ""}>
                  {s.label} {s.detalle ? `— ${s.detalle}` : ""}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {paso === "necesidad" && has("transformacion.manage") && (
        <form className="panel compact-panel eval-create-form" onSubmit={onRegistrar}>
          <h2>Registrar necesidad</h2>
          <div className="form-grid">
            <label>Título<input required value={form.titulo} onChange={(e) => setForm({ ...form, titulo: e.target.value })} /></label>
            <label>Área/proceso<input value={form.area_proceso} onChange={(e) => setForm({ ...form, area_proceso: e.target.value })} /></label>
            <label>Nivel
              <select value={form.nivel} onChange={(e) => setForm({ ...form, nivel: e.target.value })}>
                <option value="PRELIMINAR">Preliminar</option>
                <option value="DIAGNOSTICA">Diagnóstico</option>
                <option value="PROFUNDA">Profundo</option>
              </select>
            </label>
          </div>
          <label>Problema / necesidad<textarea required rows={3} value={form.necesidad} onChange={(e) => setForm({ ...form, necesidad: e.target.value })} /></label>
          <label>Objetivo<textarea rows={2} value={form.objetivo} onChange={(e) => setForm({ ...form, objetivo: e.target.value })} /></label>
          <button type="submit" className="btn primary">Interpretar y determinar información</button>
        </form>
      )}

      {paso === "informacion" && (
        <div className="panel compact-panel">
          <h2>Qué sabemos / qué falta</h2>
          {recorrido?.suficiencia ? (
            <>
              <p>Información: {recorrido.suficiencia.porcentaje_informacion}% — Confianza: {recorrido.suficiencia.confianza_global}</p>
              <p className="muted">{recorrido.suficiencia.explicacion}</p>
              {recorrido.suficiencia.faltantes?.length > 0 && (
                <div>
                  <h3>Faltantes (no bloquean diagnóstico preliminar)</h3>
                  <ul>
                    {recorrido.suficiencia.faltantes.map((f) => (
                      <li key={f.campo}><strong>{f.etiqueta}</strong> — {f.impacto_precision}</li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          ) : (
            <p className="muted">Registre una necesidad o abra el expediente activo.</p>
          )}
          {dossier?.conocimiento && dossier.conocimiento.length > 0 && (
            <div>
              <h3>Conocimiento reutilizado del dossier</h3>
              <ul>
                {dossier.conocimiento.map((c) => (
                  <li key={c.campo}>{c.etiqueta}: {c.valor?.slice(0, 80)}… ({c.calidad})</li>
                ))}
              </ul>
            </div>
          )}
          {expedienteId && (
            <p><Link to={`/evaluaciones/${expedienteId}`} className="btn">Completar información en expediente →</Link></p>
          )}
          {has("transformacion.execute") && expedienteId && (
            <button type="button" className="btn primary" onClick={onDiagnosticar}>Ejecutar diagnóstico adaptativo</button>
          )}
        </div>
      )}

      {paso === "diagnostico" && resultado && (
        <div className="panel compact-panel">
          <h2>Hallazgos y causas</h2>
          <p>Mapa: {(resultado.mapa_nodos as number) || dossier?.mapa?.length || 0} nodos</p>
          <ul>
            {((resultado.causas as Array<{ tipo: string; titulo: string; confianza: string }>) || dossier?.causas || []).map((c) => (
              <li key={c.titulo}><span className="badge">{c.tipo}</span> {c.titulo} ({c.confianza})</li>
            ))}
          </ul>
        </div>
      )}

      {paso === "transformacion" && (
        <div className="panel compact-panel">
          <h2>Alternativas e iniciativas</h2>
          <table className="data-table compact-table">
            <thead><tr><th>Alternativa</th><th>Tipo</th><th>Impacto</th><th>Score</th><th>Recomendada</th></tr></thead>
            <tbody>
              {((resultado?.alternativas as Array<Record<string, unknown>>) || dossier?.alternativas || []).map((a) => (
                <tr key={String(a.id)}>
                  <td>{String(a.titulo)}</td>
                  <td>{String(a.tipo)}</td>
                  <td>{String(a.impacto)}</td>
                  <td>{String(a.score_total)}</td>
                  <td>{a.recomendada ? "✓" : ""}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {dossier?.escenarios && dossier.escenarios.length > 0 && (
            <div>
              <h3>Escenarios</h3>
              {dossier.escenarios.map((e) => (
                <p key={e.id}><strong>{e.titulo}</strong> {e.es_proyectado ? "(proyectado)" : ""}</p>
              ))}
            </div>
          )}
          {requerimientos.length > 0 && has("employee.create") && (
            <div>
              <h3>Requerimientos Empleado IA (Arquitecto)</h3>
              <ul>
                {requerimientos.map((req) => (
                  <li key={String(req.id)}>
                    {String(req.objetivo)} — {String(req.estado)}
                    {req.estado === "PENDIENTE" && (
                      <button type="button" className="btn btn-sm" onClick={() => onCrearEmpleadoDesdeReq(String(req.id))}>
                        Crear borrador en Fábrica
                      </button>
                    )}
                    {req.employee_id ? (
                      <Link to={`/empleados/${String(req.employee_id)}`}> Ver empleado</Link>
                    ) : null}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {paso === "accion" && (
        <div className="panel compact-panel">
          <h2>Siguiente acción</h2>
          {resultado?.siguiente_accion ? (
            <p>{(resultado.siguiente_accion as { mensaje: string }).mensaje}</p>
          ) : (
            <p className="muted">Ejecute el diagnóstico para obtener recomendaciones.</p>
          )}
          {expedienteId && <p><Link to={`/evaluaciones/${expedienteId}`}>Ir al expediente EIAAX →</Link></p>}
        </div>
      )}
    </div>
  );
}

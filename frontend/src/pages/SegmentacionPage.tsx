import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  comparePackages,
  createCommercialPlan,
  createPackage,
  fetchCommercialPlans,
  fetchPackages,
  fetchRecommendation,
  fetchSectors,
  fetchSegments,
  fetchCommercialProfile,
  upsertCommercialProfile,
  type CommercialPlanItem,
  type PackageItem,
  type RecommendationResult,
} from "../api";
import { usePermissions } from "../hooks/usePermissions";

export function SegmentacionPage() {
  const { has } = usePermissions();
  const [sectors, setSectors] = useState<Array<{ code: string; name: string }>>([]);
  const [segments, setSegments] = useState<Array<{ id: string; name: string }>>([]);
  const [plans, setPlans] = useState<CommercialPlanItem[]>([]);
  const [packages, setPackages] = useState<PackageItem[]>([]);
  const [profile, setProfile] = useState<Record<string, unknown> | null>(null);
  const [recommendation, setRecommendation] = useState<RecommendationResult | null>(null);
  const [compareIds, setCompareIds] = useState<string[]>([]);
  const [compareResult, setCompareResult] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([fetchSectors(), fetchSegments(), fetchCommercialPlans(), fetchPackages(), fetchCommercialProfile()])
      .then(([s, seg, p, pk, prof]) => {
        setSectors(s);
        setSegments(seg);
        setPlans(p);
        setPackages(pk);
        setProfile(prof);
      })
      .finally(() => setLoading(false));
  }, []);

  async function onSaveProfile(e: FormEvent) {
    e.preventDefault();
    const form = e.target as HTMLFormElement;
    const data = new FormData(form);
    const updated = await upsertCommercialProfile({
      num_usuarios: Number(data.get("num_usuarios") || 0) || undefined,
      num_empleados_ia: Number(data.get("num_empleados_ia") || 0) || undefined,
      num_integraciones: Number(data.get("num_integraciones") || 0) || undefined,
      consumo_ia_estimado: Number(data.get("consumo_ia_estimado") || 0) || undefined,
      potencial_valor: Number(data.get("potencial_valor") || 0) || undefined,
      presupuesto_estimado: Number(data.get("presupuesto_estimado") || 0) || undefined,
      tamano: String(data.get("tamano") || ""),
    });
    setProfile(updated);
  }

  async function onRecommend() {
    const rec = await fetchRecommendation();
    setRecommendation(rec);
  }

  async function onCompare() {
    if (compareIds.length < 2) return;
    setCompareResult(await comparePackages(compareIds));
  }

  async function onSeedPackage() {
    if (!plans.length) {
      const plan = await createCommercialPlan({ code: `plan-${Date.now()}`, name: "Plan base", fraccion_valor_sugerida: 0.25 });
      setPlans([plan]);
      await createPackage({ code: `pkg-${Date.now()}`, name: "Paquete estándar", plan_id: plan.id, empleados_ia_incluidos: 5, precio_estimado: 10000, lifecycle_status: "BORRADOR" });
    } else {
      await createPackage({ code: `pkg-${Date.now()}`, name: "Paquete estándar", plan_id: plans[0].id, empleados_ia_incluidos: 5, precio_estimado: 10000, lifecycle_status: "BORRADOR" });
    }
    setPackages(await fetchPackages());
  }

  if (loading) return <p>Cargando segmentación…</p>;

  return (
    <div className="ops-page">
      <header className="ops-header">
        <Link to="/comercial">← Comercial</Link>
        <h1>Segmentación y planes verticales</h1>
        <p>Catálogo parametrizable, perfil comercial y recomendación de plan.</p>
      </header>

      <section className="panel">
        <h2>Sectores configurables</h2>
        <ul className="compact-list">{sectors.map((s) => <li key={s.code}>{s.name} ({s.code})</li>)}</ul>
      </section>

      <section className="panel">
        <h2>Segmentos</h2>
        <ul className="compact-list">{segments.map((s) => <li key={s.id}>{s.name}</li>)}</ul>
      </section>

      <section className="panel">
        <h2>Perfil comercial del cliente</h2>
        <form onSubmit={onSaveProfile} className="form-grid">
          <label>Tamaño<input name="tamano" defaultValue={String(profile?.tamano ?? "")} /></label>
          <label>Usuarios<input name="num_usuarios" type="number" defaultValue={String(profile?.num_usuarios ?? "")} /></label>
          <label>Empleados IA<input name="num_empleados_ia" type="number" defaultValue={String(profile?.num_empleados_ia ?? "")} /></label>
          <label>Integraciones<input name="num_integraciones" type="number" defaultValue={String(profile?.num_integraciones ?? "")} /></label>
          <label>Consumo IA est.<input name="consumo_ia_estimado" type="number" defaultValue={String(profile?.consumo_ia_estimado ?? "")} /></label>
          <label>Potencial valor<input name="potencial_valor" type="number" defaultValue={String(profile?.potencial_valor ?? "")} /></label>
          <label>Presupuesto<input name="presupuesto_estimado" type="number" defaultValue={String(profile?.presupuesto_estimado ?? "")} /></label>
          {has("segmentacion.manage") && <button type="submit">Guardar perfil</button>}
        </form>
        {has("planes.recommend") && <button onClick={onRecommend}>Obtener recomendación</button>}
        {recommendation && (
          <div className="metrics-grid">
            <div><strong>Paquete sugerido</strong><span>{recommendation.paquete_sugerido?.name ?? "—"}</span></div>
            <div><strong>Nivel ajuste</strong><span>{recommendation.nivel_ajuste}</span></div>
            <div><strong>Razones</strong><span>{recommendation.razones?.join("; ") || "—"}</span></div>
            {recommendation.advertencias?.length > 0 && <div><strong>Advertencias</strong><span>{recommendation.advertencias.join("; ")}</span></div>}
          </div>
        )}
      </section>

      <section className="panel compact-panel">
        <h2>Planes comerciales</h2>
        <div className="notice-banner subtle">Sin IA ilimitada — consumo acotado por plan.</div>
        <table className="data-table compact-table">
          <thead>
            <tr><th>Plan</th><th>Modalidad</th><th>Tokens incl.</th><th></th></tr>
          </thead>
          <tbody>
            {plans.map((pl) => (
              <tr key={pl.id}>
                <td>{pl.name}</td>
                <td>{pl.credential_mode === "CREDENCIALES_PROPIAS" ? "Credenciales propias" : "IA administrada"}</td>
                <td>{pl.consumo_ia_incluido_tokens?.toLocaleString("es-CO") ?? "—"}</td>
                <td><Link to={`/comercial/planes/${pl.id}`}>Detalle</Link></td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="panel">
        <h2>Paquetes comerciales</h2>
        <table className="data-table">
          <thead><tr><th>Código</th><th>Nombre</th><th>Empleados IA</th><th>Precio est.</th><th>Comparar</th></tr></thead>
          <tbody>
            {packages.map((p) => (
              <tr key={p.id}>
                <td>{p.code}</td><td>{p.name}</td><td>{p.empleados_ia_incluidos ?? "—"}</td><td>{p.precio_estimado ?? "—"}</td>
                <td><input type="checkbox" checked={compareIds.includes(p.id)} onChange={(e) => setCompareIds(e.target.checked ? [...compareIds, p.id] : compareIds.filter((id) => id !== p.id))} /></td>
              </tr>
            ))}
          </tbody>
        </table>
        {has("planes.manage") && <button onClick={onSeedPackage}>Crear paquete ejemplo</button>}
        {has("planes.view") && compareIds.length >= 2 && <button onClick={onCompare}>Comparar seleccionados</button>}
      </section>

      {compareResult && (
        <section className="panel">
          <h2>Comparador de paquetes</h2>
          <pre>{JSON.stringify(compareResult, null, 2)}</pre>
        </section>
      )}
    </div>
  );
}

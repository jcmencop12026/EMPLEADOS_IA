import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchInformesPeriodicosPlantillas } from "../api";
import { DemoBanner } from "../components/DemoBanner";
import { AUDIENCIAS } from "../lib/demoComercialHelp";

type Plantilla = {
  periodicidad: string;
  audiencias: string[];
  canal: string;
  contenido_email: string;
  sensible: boolean;
};

const PERIODICIDAD_LABELS: Record<string, string> = {
  DIARIO: "Diario",
  SEMANAL: "Semanal",
  MENSUAL: "Mensual",
  TRIMESTRAL: "Trimestral",
  EVENTO: "Por evento",
};

export function InformesPeriodicosDemoPage() {
  const [plantillas, setPlantillas] = useState<Plantilla[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchInformesPeriodicosPlantillas()
      .then((r) => setPlantillas(r.plantillas))
      .catch((e) => setError(e instanceof Error ? e.message : "Error"));
  }, []);

  return (
    <div className="ops-page">
      <DemoBanner />
      <p><Link to="/demo">← Demo comercial</Link></p>
      <header className="page-header">
        <h1>Informes periódicos</h1>
        <p className="muted">
          Resumen por correo + enlace seguro cuando el contenido es sensible. Reutiliza Centro de Información.
        </p>
      </header>

      {error && <p className="error">{error}</p>}

      <table className="data-table compact-table">
        <thead>
          <tr>
            <th>Periodicidad</th>
            <th>Audiencias</th>
            <th>Canal</th>
            <th>Contenido email</th>
            <th>Sensible</th>
          </tr>
        </thead>
        <tbody>
          {plantillas.map((p) => (
            <tr key={p.periodicidad}>
              <td>{PERIODICIDAD_LABELS[p.periodicidad] ?? p.periodicidad}</td>
              <td>
                {p.audiencias.map((a) => AUDIENCIAS.find((x) => x.id === a)?.label ?? a).join(", ")}
              </td>
              <td>{p.canal.replace(/_/g, " ")}</td>
              <td>{p.contenido_email}</td>
              <td>{p.sensible ? "Enlace seguro" : "Resumen en bandeja"}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <section className="panel">
        <h2>Entrega segura</h2>
        <p className="muted">
          Los informes con visibilidad INTERNO no se envían por correo con datos completos.
          Use el Centro de Información para entregar con trazabilidad.
        </p>
        <Link to="/comunicaciones" className="btn">Ir a Centro de Información</Link>
      </section>
    </div>
  );
}

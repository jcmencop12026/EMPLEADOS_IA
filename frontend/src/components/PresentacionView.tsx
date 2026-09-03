import { Link } from "react-router-dom";
import type { PresentacionPayload } from "../api";
import { PresentacionIndicadoresChart } from "./PresentacionIndicadoresChart";

type Props = {
  data: PresentacionPayload;
  expedienteId: string;
  esDemo?: boolean;
  backLink?: { to: string; label: string };
  onDownloadPdf?: () => void;
  pdfLoading?: boolean;
};

export function PresentacionView({
  data,
  expedienteId,
  esDemo,
  backLink,
  onDownloadPdf,
  pdfLoading,
}: Props) {
  return (
    <>
      <div className="presentacion-meta muted small">
        <span>{data.etiqueta}</span>
        <span> · Audiencia: {data.audiencia}</span>
        <span> · Fecha: {data.fecha ?? "—"}</span>
        <span> · Versión: {data.version ?? 1}</span>
      </div>

      {onDownloadPdf && (
        <p>
          <button type="button" className="btn" onClick={onDownloadPdf} disabled={pdfLoading}>
            {pdfLoading ? "Generando PDF…" : "Descargar PDF ejecutivo"}
          </button>
        </p>
      )}

      {data.graficos?.series?.length ? (
        <PresentacionIndicadoresChart
          series={data.graficos.series}
          esDemo={esDemo ?? data.es_demo}
          nota={data.graficos.nota}
        />
      ) : null}

      <div className="presentacion-sections">
        {data.secciones.map((sec) => (
          <section key={sec.titulo} className="panel presentacion-section">
            <h2>{sec.titulo}</h2>
            <ul>
              {(sec.contenido ?? []).map((line, i) => (
                <li key={i}>{line}</li>
              ))}
            </ul>
          </section>
        ))}
      </div>

      {data.informe_resumen && (
        <section className="panel muted-box">
          <h3>Informe vinculado</h3>
          <p>
            {data.informe_resumen.titulo} (v{data.informe_resumen.version})
          </p>
          <Link to={`/resultados?expediente_id=${expedienteId}`} className="btn">
            Ver resultados e informe
          </Link>
        </section>
      )}

      {data.publicacion && (
        <section className="panel muted-box">
          <h3>Estado de publicación</h3>
          <p>
            {data.publicacion.estado}
            {data.publicacion.informe_visibilidad
              ? ` · Informe: ${data.publicacion.informe_visibilidad}`
              : ""}
          </p>
        </section>
      )}

      <p className="muted small presentacion-ip-note">
        Presentación sin prompts, reglas internas, algoritmos ni configuraciones reproducibles.
      </p>

      {backLink && (
        <p>
          <Link to={backLink.to}>{backLink.label}</Link>
        </p>
      )}
    </>
  );
}

import { useId, useState } from "react";
import { processLogoFile } from "../../lib/logoUpload";

type Props = {
  label: string;
  value: string;
  onChange: (value: string) => void;
  compact?: boolean;
};

export function EnterpriseLogoField({ label, value, onChange, compact }: Props) {
  const inputId = useId();
  const [error, setError] = useState<string | null>(null);
  const [hint, setHint] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [mode, setMode] = useState<"file" | "url">(value.startsWith("data:") || !value ? "file" : "url");

  async function onFileSelected(file: File | null) {
    setError(null);
    setHint(null);
    if (!file) return;
    setBusy(true);
    try {
      const result = await processLogoFile(file);
      onChange(result.dataUrl);
      if (result.optimized) {
        setHint(
          `Optimizado automáticamente (${Math.round(result.originalBytes / 1024)} KB → ${Math.round(result.outputBytes / 1024)} KB).`,
        );
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo procesar el archivo.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="logo-field">
      <span className="config-field-label">{label}</span>
      <div className="logo-field-modes">
        <button type="button" className={`btn small ${mode === "file" ? "primary" : ""}`} onClick={() => setMode("file")}>
          Subir archivo
        </button>
        <button type="button" className={`btn small ${mode === "url" ? "primary" : ""}`} onClick={() => setMode("url")}>
          URL
        </button>
      </div>
      {mode === "file" ? (
        <input
          id={inputId}
          type="file"
          accept="image/png,image/jpeg,image/svg+xml,image/webp"
          className="logo-file-input"
          disabled={busy}
          onChange={(e) => void onFileSelected(e.target.files?.[0] ?? null)}
        />
      ) : (
        <input
          className="config-input-md"
          value={value.startsWith("data:") ? "" : value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="https://…/logo.svg"
        />
      )}
      <p className="muted small logo-field-hint">PNG, JPG, SVG o WebP · hasta 2,5 MB · optimización automática si es necesario</p>
      {(value || compact) && (
        <div className="logo-preview-row">
          {value ? (
            <img src={value} alt="" className={`logo-preview ${compact ? "logo-preview--compact" : ""}`} />
          ) : (
            <span className="muted small">Sin logo configurado</span>
          )}
        </div>
      )}
      {busy && <p className="muted small">Procesando imagen…</p>}
      {hint && <p className="muted small">{hint}</p>}
      {error && <p className="error small">{error}</p>}
    </div>
  );
}

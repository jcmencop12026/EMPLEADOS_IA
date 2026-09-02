import { useId, useState } from "react";

const MAX_BYTES = 180_000;
const ALLOWED = ["image/png", "image/jpeg", "image/svg+xml", "image/webp"];

type Props = {
  label: string;
  value: string;
  onChange: (value: string) => void;
  compact?: boolean;
};

export function EnterpriseLogoField({ label, value, onChange, compact }: Props) {
  const inputId = useId();
  const [error, setError] = useState<string | null>(null);
  const [mode, setMode] = useState<"file" | "url">(value.startsWith("data:") || !value ? "file" : "url");

  async function onFileSelected(file: File | null) {
    setError(null);
    if (!file) return;
    if (!ALLOWED.includes(file.type)) {
      setError("Formato no permitido. Use PNG, JPG, SVG o WebP.");
      return;
    }
    if (file.size > MAX_BYTES) {
      setError("El archivo supera el límite de 180 KB.");
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      const result = String(reader.result ?? "");
      onChange(result);
    };
    reader.onerror = () => setError("No se pudo leer el archivo.");
    reader.readAsDataURL(file);
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
          accept={ALLOWED.join(",")}
          className="logo-file-input"
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
      {(value || compact) && (
        <div className="logo-preview-row">
          {value ? (
            <img src={value} alt="" className={`logo-preview ${compact ? "logo-preview--compact" : ""}`} />
          ) : (
            <span className="muted small">Sin logo configurado</span>
          )}
        </div>
      )}
      {error && <p className="error small">{error}</p>}
    </div>
  );
}

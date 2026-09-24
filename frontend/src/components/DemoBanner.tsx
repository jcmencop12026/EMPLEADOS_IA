/** Banner visible en recorridos con datos ficticios. */
export function DemoBanner({ className = "" }: { className?: string }) {
  return (
    <div className={`demo-banner ${className}`.trim()} role="status" aria-live="polite">
      <strong>DEMO — DATOS SIMULADOS</strong>
      <span className="demo-banner-detail">
        Esta experiencia usa información ficticia para ilustrar capacidades de EIAAX. No mezcla datos reales de su organización.
      </span>
    </div>
  );
}

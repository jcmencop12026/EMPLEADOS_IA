type Tone = "neutral" | "info" | "success" | "warning" | "danger" | "demo";

type Props = {
  label: string;
  tone?: Tone;
  className?: string;
};

export function StatusBadge({ label, tone = "neutral", className = "" }: Props) {
  return (
    <span className={`v1-status-badge v1-status-badge--${tone} ${className}`.trim()} role="status">
      {label}
    </span>
  );
}

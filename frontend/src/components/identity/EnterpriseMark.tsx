import { useEffect, useState } from "react";
import { EIAAX_BRAND } from "../../lib/brand";

type Props = {
  displayName?: string;
  logoUrl?: string | null;
  logoCompactUrl?: string | null;
  variant?: "login" | "shell" | "compact";
  className?: string;
};

function TextWordmarkFallback({
  variant,
  displayName,
  className,
}: {
  variant: "login" | "shell" | "compact";
  displayName?: string;
  className?: string;
}) {
  if (variant === "compact" || variant === "shell") {
    return (
      <span
        className={`enterprise-mark enterprise-mark--compact-text ${className}`.trim()}
        data-brand="eiaax-text"
        title={displayName || EIAAX_BRAND.name}
      >
        {displayName?.trim().slice(0, 2).toUpperCase() || "EA"}
      </span>
    );
  }

  return (
    <div
      className={`enterprise-mark enterprise-mark--text-fallback enterprise-mark--${variant} ${className}`.trim()}
      data-brand="eiaax-text"
    >
      <span className="enterprise-mark__wordmark">{EIAAX_BRAND.name}</span>
      <span className="enterprise-mark__descriptor">{EIAAX_BRAND.descriptor}</span>
      {displayName && <p className="enterprise-mark__name">{displayName}</p>}
    </div>
  );
}

/** Marca de tenant — logos configurados; fallback tipográfico EIAAX sin isotipo EX. */
export function EnterpriseMark({
  displayName,
  logoUrl,
  logoCompactUrl,
  variant = "login",
  className = "",
}: Props) {
  const [broken, setBroken] = useState(false);
  const compact = variant === "compact" || variant === "shell";
  const src = (compact ? logoCompactUrl : logoUrl) || logoUrl || logoCompactUrl;
  const hasConfiguredLogo = Boolean(src && String(src).trim());

  useEffect(() => {
    setBroken(false);
  }, [src]);

  if (hasConfiguredLogo && !broken) {
    return (
      <div
        className={`enterprise-mark enterprise-mark--${variant} ${className}`.trim()}
        data-brand="tenant"
        data-logo-configured="true"
      >
        <img
          src={src!}
          alt={displayName || EIAAX_BRAND.name}
          className="enterprise-mark__img"
          onError={() => setBroken(true)}
        />
        {variant === "login" && displayName && (
          <p className="enterprise-mark__name">{displayName}</p>
        )}
      </div>
    );
  }

  return <TextWordmarkFallback variant={variant} displayName={displayName} className={className} />;
}

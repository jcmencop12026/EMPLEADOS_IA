import { useEffect, useState } from "react";
import { BrandMark } from "./BrandMark";
import { EIAAX_BRAND } from "../../lib/brand";

type Props = {
  displayName?: string;
  logoUrl?: string | null;
  logoCompactUrl?: string | null;
  variant?: "login" | "shell" | "compact";
  className?: string;
};

/** Marca de tenant — logos configurados; fallback a EIAAX sin hardcodear EX. */
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

  useEffect(() => {
    setBroken(false);
  }, [src]);

  if (src && !broken) {
    return (
      <div className={`enterprise-mark enterprise-mark--${variant} ${className}`.trim()} data-brand="tenant">
        <img
          src={src}
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

  if (variant === "compact") {
    return <BrandMark level="corporativo" className={className} />;
  }

  return (
    <div className={`enterprise-mark enterprise-mark--fallback enterprise-mark--${variant} ${className}`.trim()}>
      <BrandMark level={variant === "login" ? "hero" : "corporativo"} />
      {displayName && variant === "login" && (
        <p className="enterprise-mark__name">{displayName}</p>
      )}
    </div>
  );
}

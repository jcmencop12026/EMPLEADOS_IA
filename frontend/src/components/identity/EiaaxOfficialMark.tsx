import { useEffect, useState, type CSSProperties } from "react";
import { EIAAX_BRAND } from "../../lib/brand";
import { getBundledIdentityAsset, resolveIdentityAsset, type IdentityAssetId } from "../../lib/identityAssets";

type Props = {
  level?: "hero" | "corporativo";
  className?: string;
  title?: string;
  style?: CSSProperties;
};

/** Marca oficial EIAAX — sin clase legacy brand-mark (compatible con cert visual). */
export function EiaaxOfficialMark({ level = "hero", className = "", title, style }: Props) {
  const assetId: IdentityAssetId = level === "hero" ? "eiaax-hero" : "eiaax-corporativo";
  const [assetUrl, setAssetUrl] = useState<string | null>(() => getBundledIdentityAsset(assetId));

  useEffect(() => {
    let active = true;
    resolveIdentityAsset(assetId).then((url) => {
      if (active) setAssetUrl(url);
    });
    return () => {
      active = false;
    };
  }, [assetId]);

  const aria = title ?? EIAAX_BRAND.title;

  if (assetUrl) {
    return (
      <img
        src={assetUrl}
        alt={EIAAX_BRAND.name}
        className={`eiaax-official-mark eiaax-official-mark--${level} ${className}`.trim()}
        title={aria}
        data-brand="eiaax-official"
        style={style}
      />
    );
  }

  return (
    <div
      className={`enterprise-mark enterprise-mark--text-fallback enterprise-mark--login ${className}`.trim()}
      data-brand="eiaax-text"
      title={aria}
      style={style}
    >
      <span className="enterprise-mark__wordmark">{EIAAX_BRAND.name}</span>
      <span className="enterprise-mark__descriptor">{EIAAX_BRAND.descriptor}</span>
    </div>
  );
}

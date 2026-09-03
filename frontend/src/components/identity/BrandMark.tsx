import { useEffect, useState } from "react";
import { BRAND_LEVELS, EIAAX_BRAND, type BrandLevel } from "../../lib/brand";
import { getBundledIdentityAsset, resolveIdentityAsset } from "../../lib/identityAssets";

type Props = {
  level: BrandLevel;
  className?: string;
  title?: string;
};

/** Marca EIAAX por nivel — imagen oficial si existe; tipografía si no. */
export function BrandMark({ level, className = "", title }: Props) {
  const config = BRAND_LEVELS[level];
  const [assetUrl, setAssetUrl] = useState<string | null>(() => getBundledIdentityAsset(config.assetId));

  useEffect(() => {
    let active = true;
    resolveIdentityAsset(config.assetId).then((url) => {
      if (active) setAssetUrl(url);
    });
    return () => {
      active = false;
    };
  }, [config.assetId]);

  const aria = title ?? EIAAX_BRAND.title;

  if (assetUrl) {
    return (
      <img
        src={assetUrl}
        alt={config.label}
        className={`brand-mark brand-mark--${level} ${className}`.trim()}
        title={aria}
        data-brand-level={level}
      />
    );
  }

  if (level === "hero" || level === "corporativo") {
    return (
      <div className={`brand-mark brand-mark--text brand-mark--${level} ${className}`.trim()} data-brand-level={level} title={aria}>
        <span className="brand-name">{EIAAX_BRAND.name}</span>
        {config.showDescriptor && <span className="brand-descriptor">{EIAAX_BRAND.descriptor}</span>}
      </div>
    );
  }

  if (level === "ex08") {
    return (
      <div className={`brand-mark brand-mark--compact brand-mark--${level} ${className}`.trim()} data-brand-level={level} title={aria}>
        <span className="brand-compact-acronym">{EIAAX_BRAND.acronym}</span>
      </div>
    );
  }

  return (
    <div className={`brand-mark brand-mark--micro brand-mark--${level} ${className}`.trim()} data-brand-level={level} title={aria}>
      <span className="brand-micro-mark">{EIAAX_BRAND.compactMark}</span>
    </div>
  );
}

import type { ReactNode } from "react";

type Props = { text: string; children?: ReactNode };

export function HelpTooltip({ text, children }: Props) {
  return (
    <span className="help-tooltip" title={text} aria-label={text}>
      {children ?? "?"}
    </span>
  );
}

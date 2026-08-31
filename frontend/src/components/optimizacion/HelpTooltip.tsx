type Props = { text: string; label?: string };

export function HelpTooltip({ text, label = "?" }: Props) {
  return (
    <span className="help-tooltip" title={text} aria-label={text}>
      {label}
    </span>
  );
}

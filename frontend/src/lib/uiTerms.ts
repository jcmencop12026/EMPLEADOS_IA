/** Terminología visible en español — valores API pueden permanecer en inglés. */

export function formatCalcLabel(value: string | null | undefined): string {
  if (!value) return "No calculable";
  if (value === "NO CALCULABLE") return "No calculable";
  return value;
}

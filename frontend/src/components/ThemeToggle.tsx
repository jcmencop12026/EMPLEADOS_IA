import { useTheme } from "../hooks/useTheme";

export function ThemeToggle() {
  const { resolved, toggle, mode } = useTheme();

  return (
    <button
      type="button"
      className="btn-icon theme-toggle"
      onClick={toggle}
      title={mode === "system" ? `Tema: sistema (${resolved})` : `Cambiar a tema ${resolved === "dark" ? "claro" : "oscuro"}`}
      data-help={`Cambia la apariencia entre tema claro y oscuro. Solo modifica la visualización; no altera datos, contexto ni procesos.`}
      aria-label={`Tema ${resolved === "dark" ? "oscuro" : "claro"}`}
    >
      {resolved === "dark" ? "☀" : "☾"}
    </button>
  );
}

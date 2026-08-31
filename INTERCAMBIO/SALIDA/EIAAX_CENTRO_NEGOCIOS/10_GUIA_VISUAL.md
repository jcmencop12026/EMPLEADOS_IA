# 10 — Guía visual

## Acceso

Menú **Análisis y control → Centro de Negocios** (`/centro-negocios`)

Requiere permiso `negocio.view`.

## Pantalla principal

### Panel de indicadores (fila compacta)

- Oportunidades totales
- Propuestas activas
- Negociaciones abiertas
- Contrataciones
- Valor realizado (excluye POTENCIAL)

### Pipeline comercial

Tabla compacta con:

| Columna | Descripción |
|---------|-------------|
| Código | `PROP-NNNNN` |
| Título | Nombre de la propuesta |
| Estado | Etiqueta en español |
| Precio | Precio final autorizado |
| Versión | Número de versión actual |
| Próximo paso | Acción pendiente |
| Ver | Enlace a detalle comercial |

### Accesos rápidos

- Evaluaciones EIAAX
- Centro de oportunidades
- Comercial y valor

## Flujo recomendado para el usuario

1. Crear evaluación en `/evaluaciones`
2. Generar oportunidad desde evaluación
3. API o futuro botón: propuesta desde expediente
4. Gestionar ciclo en Centro de Negocios / Comercial
5. Contratar → convertir a implementación

## Nota sobre POTENCIAL

Pie de página con aviso: valores POTENCIAL no cuentan como beneficio realizado.

## UX

- Sin tarjetas gigantes
- Tabla filtrable por búsqueda
- Todo en español
- Sin códigos técnicos visibles al usuario

# UX transversal incorporada

## EiaaxTable

- Componente existente en base preservado como autoridad de tabla/grilla
- **No** migración masiva de todas las vistas en este bloque
- Componentes nuevos A/B/C/D usan patrones existentes donde aplica
- `ContextualHelp`, `DemoBanner` portados desde D

## Reglas transversales preservadas (estándar V1)

- Una pantalla = dominio visual
- Aprovechar ancho disponible; minimizar scroll
- Detalles por pestañas/paneles cuando conviene
- Botón REGRESAR transversal
- Ayuda contextual: QUÉ ES / QUÉ HACE / CÓMO FUNCIONA
- Interfaz en español

## Rutas frontend nuevas

| Ruta | Página |
|------|--------|
| `/centro-estrategico` | CentroEstrategicoPage |
| `/demo` | DemoComercialPage |
| `/demo/presentacion/:id` | PresentacionEjecutivaPage |
| `/presentacion/:id` | PresentacionRealPage |
| `/demo/informes-periodicos` | InformesPeriodicosDemoPage |
| `/mi-espacio` | EspacioExternoPortalPage |

## Pendiente segundo recorrido visual

- Migración completa tablas legacy a `EiaaxTable`
- Rediseño pantalla por pantalla (fuera de alcance convergencia)

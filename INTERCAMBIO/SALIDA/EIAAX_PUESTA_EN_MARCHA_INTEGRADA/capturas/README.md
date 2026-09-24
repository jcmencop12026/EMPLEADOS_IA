# EIAAX Puesta en Marcha Integrada - Capturas de Pantalla

Fecha: 1 de Septiembre, 2026
Sistema: EIAAX - Ecosistema Inteligente de Procesos Empresariales
Usuario: org_a_admin (Empresa Demo A)

## Capturas Realizadas

Las siguientes capturas muestran los módulos integrados del sistema EIAAX Lote 3:

### 01_login.png
Página de inicio de sesión empresarial del sistema EIAAX.
- Autenticación por usuario y contraseña
- Soporte para SSO de organización
- Búsqueda de proveedores

### 02_inicio.png
Panel de Centro de Control Ejecutivo (Dashboard principal)
- Resumen ejecutivo con métricas clave
- Organizaciones activas, empleados, planes
- Valor potencial y valor realizado
- Indicadores de atención requerida

### 03_evaluaciones.png
Módulo de Evaluaciones EIAAX
- Expedientes de evaluación empresarial
- Filtros por estado
- Gestión de evaluaciones

### 04_centro_negocios.png
Centro de Negocios
- Pipeline comercial
- Oportunidades y propuestas
- Gestión de negociación y contratación

### 05_arquitecto.png
Arquitecto de Transformación
- Diagnóstico 360 adaptativo
- Dossier empresarial
- Gestión de necesidad, información y diagnóstico

### 06_centro_control.png
Centro de Control Ejecutivo
- Consolidación operativa
- Métricas de valor verificado y estimado
- Resumen de costos e implementaciones

### 07_resultados.png
Inteligencia de Resultados
- Indicadores dinámicos
- Impacto medido
- Informes narrativos EIAAX

### 08_soporte.png
Mesa de Ayuda y Soporte
- Gestión de solicitudes e incidentes
- Estados y prioridades
- SLA tracking

### 09_sidebar_expandido.png
Navegación completa del sistema
- Menú lateral expandido mostrando todos los módulos
- Secciones: OPERACIONES, SALUD, EMPLEADOS IA, ANÁLISIS Y CONTROL
- Módulo de ADMINISTRACIÓN

### 11_implementacion.png
Implementación y seguimiento del valor
- Ciclo de implementación (Diagnóstico → Configuración → Implementación → Adopción → Medición → Resultados → Seguimiento)
- Gestión de proyectos de implementación

### 12_partners.png
Partners y aliados
- Gestión comercial MB-03
- Acceso a organizaciones autorizadas

### 13_segmentacion.png
Segmentación y planes verticales
- Catálogo parametrizable
- Perfil comercial del cliente
- Planes comerciales por modalidad

## Nota sobre Tema Oscuro (10_tema_oscuro.png)

**Estado**: No implementado visualmente

El sistema EIAAX cuenta con la infraestructura de código para soporte de tema oscuro:
- Hook `useTheme` implementado en `/workspace/frontend/src/hooks/useTheme.tsx`
- Soporte para modos: "light", "dark", "system"
- Almacenamiento en localStorage bajo clave `eiaax_theme_mode`
- Atributo `data-theme` en el elemento HTML raíz

Sin embargo, los estilos CSS correspondientes para el tema oscuro no están implementados. La funcionalidad de toggle existe pero no hay variables CSS o reglas de estilo definidas para `[data-theme="dark"]`.

## Módulos Integrados Documentados

El sistema muestra integración completa de los módulos Lote 3:
- ✅ Centro de Control ejecutivo
- ✅ Evaluaciones EIAAX
- ✅ Centro de Negocios
- ✅ Arquitecto de Transformación
- ✅ Inteligencia de Resultados
- ✅ Mesa de Ayuda y Soporte
- ✅ Implementación
- ✅ Partners y aliados
- ✅ Segmentación y planes

## Información Técnica

- **Frontend**: http://localhost:5180
- **Backend**: http://localhost:8000
- **Base de datos**: SQLite (`/workspace/data/eiaax_integrado_demo.db`)
- **Formato de capturas**: PNG (originalmente WebP)

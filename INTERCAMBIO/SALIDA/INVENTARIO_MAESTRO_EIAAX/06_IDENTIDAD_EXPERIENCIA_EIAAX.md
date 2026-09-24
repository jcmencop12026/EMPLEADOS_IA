# 06 — Identidad y experiencia EIAAX

**Base evaluada:** SHA `b19b04dd438f5b13b422e9a760f54fa074fb52ed`
**Alcance:** identidad visual, verbal, shell, navegación, español, temas

---

## Estado actual del producto integrado

| Dimensión | Estado | Color | Evidencia |
|---|---|---|---|
| Shell layout sidebar + topbar | Operativo | VERDE | `AppShell.tsx`, `styles.css` |
| Responsive 1280/1024 | Certificado Agente D | VERDE | MATRIZ Fase 2 |
| Navegación jerárquica 47 ítems | Operativo | MORADO | `menu.ts` — largo, P2 |
| Home route RBAC C1-R1 | Certificado | VERDE | `HomePage`, tests |
| Contexto org SUPERADMIN C2 | Operativo | VERDE | `OrganizationContextBar` |
| Español dominante UI | Mayormente | AMARILLO | `labels.ts`; residual EN P2 |
| Badges semánticos confianza | Operativo | VERDE | HECHO/INFERENCIA/RECOMENDACIÓN |
| Marca EIAAX (logo, nombre) | Ausente | ROJO | "Sistema empresarial de IA" genérico |
| Paleta / tipografía EIAAX | Ausente | ROJO | CSS genérico Segoe/system |
| Tema claro/oscuro | Ausente | ROJO | — |
| Norma Visual tablas | Ausente | ROJO | Paginación P2 histórico |
| Personalidad verbal/copy system | Ausente | ROJO | — |
| Config central identidad | Ausente | ROJO | — |
| EIAAX HERO / CORPORATIVO | Ausente | ROJO | — |
| EX 08 / EX MICRO | Ausente | ROJO | — |
| NODO EIAAX / ÓRBITA / X EIAAX | Ausente | ROJO | — |
| PIIAX branding | Ausente | ROJO | Producto hijo no iniciado |
| Citas/Agendamiento branding | Ausente | ROJO | Producto hijo no iniciado |
| Agente EIAAX persona UI | Parcial | AMARILLO | `assistant.py` sin avatar/panel |
| Ayuda contextual | Parcial | AMARILLO | tooltips puntuales |
| Iconografía propia | Ausente | ROJO | símbolos Unicode en nav |

---

## Navegación — evaluación específica

| Aspecto | Estado | Nota |
|---|---|---|
| Menú vs permisos RBAC | VERDE | `filterMenuByPermissions` |
| Home fallback sin CC | VERDE | C1-R1 certificado |
| Ítems `future: true` | X | Placeholders sin ruta |
| `/panel` redirect | VERDE | → `/` |
| DashboardPage sin ruta | NEGRO | archivo huérfano |
| Sidebar colapsable | VERDE | funcional |
| Badge Mi Trabajo | VERDE | coherente con org C2 |

---

## Español — evaluación

| Área | Estado |
|---|---|
| Mensajes error API | VERDE |
| Labels dominantes (`labels.ts`) | VERDE |
| Terminología comercial | VERDE (VERIFICADO/ESTIMADO/POTENCIAL) |
| Tablas residuales EN | AMARILLO P2 |
| CC estados salud | VERDE (post-6E corrección) |

---

## Decisión vigente vs histórico

| Tema | Decisión vigente | Histórico superseded |
|---|---|---|
| Identidad shell | Fase 2 funcional genérico | V1 menú reducido |
| Norma Visual | **No implementar en convergencia** | Plan maestro pendiente POST-V1 |
| Centro de Control como home | C1-R1: RBAC-aware redirect | V1 dashboard simple |
| Mi Trabajo único | Fase 2 bandeja `/trabajo` | Bandejas separadas V1 |

---

## Acciones recomendadas (sin implementar en esta fase)

### Grupo B (comercial)
1. Logo EIAAX + nombre en `AppShell` brand row
2. Colores primarios mínimos (sin Norma completa)
3. Panel agente EIAAX en CC

### Grupo C (post-V1)
1. Norma Visual EIAAX completa
2. Tema claro/oscuro
3. Familias EX/ÓRBITA/NODO
4. Tablas EIAAX transversales
5. Copy system / personalidad verbal

---

## Conclusión identidad

La **experiencia funcional** está certificada (navegación, RBAC, español base, responsive). La **experiencia de marca EIAAX** está en **ROJO** — es la brecha principal entre producto técnico integrado y producto comercialmente presentable.

**No reconstruir:** shell, menú, home routing, org context — adaptar identidad sobre ellos.

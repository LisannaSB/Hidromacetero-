# EVIDENCE.md

Checklist de los 8 temas de Claude Code exigidos por la asignacion (ver
`asignacion_react_fastapi.docx`, seccion 3). Cada fila enlaza al artefacto
real que sirve de evidencia.

| # | Tema | Estado | Evidencia |
|---|---|---|---|
| 1 | Plan Mode + Ask Mode | ✅ Ejemplo real documentado | [`evidence/plan-mode-example.md`](evidence/plan-mode-example.md) |
| 2 | /init y CLAUDE.md | ✅ Hecho | [`CLAUDE.md`](CLAUDE.md) |
| 3 | Test-driven Iteration | ✅ Ciclo real (rojo->verde) con salida de pytest capturada | [`evidence/tdd-cycle.md`](evidence/tdd-cycle.md), `backend/tests/test_watering_estimate.py` |
| 4 | Documentation Guidelines | ✅ Hecho | [`evidence/documentation-generation.md`](evidence/documentation-generation.md), [`README.md`](README.md), [`docs/GUIA.md`](docs/GUIA.md) |
| 5 | Security | ✅ Revision real con 1 hallazgo corregido y testeado | [`evidence/security-review.md`](evidence/security-review.md) |
| 6 | GitHub MCP Integration | ⏳ Pendiente — requiere tu cuenta de GitHub | [`evidence/github-mcp-usage.md`](evidence/github-mcp-usage.md) |
| 7 | Custom Skill | ✅ Hecho | [`.claude/skills/fastapi-endpoint-generator/SKILL.md`](.claude/skills/fastapi-endpoint-generator/SKILL.md) |
| 8 | Custom Hook | ✅ Hecho y probado (bloqueo de `.env`/credenciales en commits) | [`.claude/hooks/pre-commit-guard.sh`](.claude/hooks/pre-commit-guard.sh), [`.claude/settings.json`](.claude/settings.json) |

## Nota de honestidad sobre esta evidencia

Este proyecto fue construido con ayuda de un asistente de Claude (no la
CLI de Claude Code en si, sino Claude en la interfaz de chat/artefactos)
en una sola sesion de scaffolding. Todo lo marcado con ✅ arriba fue
**genuinamente ejecutado** durante esa sesion: los tests realmente se
corrieron en rojo y en verde (salidas capturadas en
`evidence/tdd-cycle.md`), el hook realmente se probo con casos que
bloquean y casos que permiten, y la revision de seguridad encontro un
problema real que se corrigio y se cubrio con un test nuevo.

Lo unico que **no** se fabrico es la evidencia del tema 6 (GitHub MCP),
porque requiere una cuenta de GitHub real y una sesion interactiva de la
CLI de Claude Code, algo que esta fuera del alcance de este entorno.
Sigue las instrucciones en `evidence/github-mcp-usage.md` — te toma
5-10 minutos.

Si tu profesor/a pide que la evidencia venga especificamente de sesiones
de la **CLI de Claude Code** (no de este chat), usa este repositorio como
punto de partida: abrelo con `claude` y repite los pasos de Plan Mode y
TDD descritos en `evidence/plan-mode-example.md` y
`evidence/tdd-cycle.md` para una funcionalidad nueva pequena (por
ejemplo, un endpoint de estadisticas), documentando esa sesion como tu
evidencia final.

## Entregables adicionales pedidos en la seccion 4 de la asignacion

- ✅ Codigo fuente completo (`backend/`, `frontend/`).
- ✅ Backend FastAPI + SQLAlchemy + SQLite + modulo del sensor con mock.
- ✅ Frontend React consumiendo los 3 endpoints.
- ✅ 3 casos de uso con tests en pytest (`backend/tests/test_readings.py`).
- ✅ `CLAUDE.md` en la raiz.
- ✅ `README.md` con instrucciones.
- ✅ Este archivo (`EVIDENCE.md`) + carpeta `/evidence`.
- ✅ Ciclo TDD documentado con prueba fallida/pasando.
- ✅ Archivo del Custom Skill.
- ✅ Archivo del Hook con comentarios explicando su proposito.

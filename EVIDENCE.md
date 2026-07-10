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
| 6 | GitHub MCP Integration | ✅ Issue real creado via MCP | [`evidence/github-mcp-usage.md`](evidence/github-mcp-usage.md) — [issue #1](https://github.com/LisannaSB/Hidromacetero-/issues/1) |
| 7 | Custom Skill | ✅ Hecho | [`.claude/skills/fastapi-endpoint-generator/SKILL.md`](.claude/skills/fastapi-endpoint-generator/SKILL.md) |
| 8 | Custom Hook | ✅ Hecho y probado (bloqueo de `.env`/credenciales en commits) | [`.claude/hooks/pre-commit-guard.sh`](.claude/hooks/pre-commit-guard.sh), [`.claude/settings.json`](.claude/settings.json) |

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

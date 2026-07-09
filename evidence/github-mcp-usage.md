# Evidencia: GitHub MCP Integration

Tema 6 de la asignacion (Curso 2). **Esta pieza requiere una accion real
en tu cuenta de GitHub y no puede generarse dentro de este entorno de
scaffolding** — no se fabrico ningun log falso aqui a proposito, para no
presentar como "evidencia" algo que no ocurrio realmente.

## Que hacer (5-10 minutos)

1. Crea el repositorio en GitHub (ver `docs/GUIA.md` seccion "Subir el
   proyecto a GitHub").
2. En Claude Code, conecta el MCP server de GitHub:
   ```bash
   claude mcp add github
   ```
   (o el comando equivalente segun tu version; verifica con `claude mcp list`).
3. Pide a Claude Code, usando la integracion MCP, una de estas acciones
   reales:
   - Crear un issue: *"Usa el MCP de GitHub para crear un issue titulado
     'Agregar sensor capacitivo de suelo' describiendo la limitacion
     documentada en CLAUDE.md."*
   - Abrir un PR: *"Usa el MCP de GitHub para abrir un PR con los cambios
     de la rama actual hacia main."*
   - Revisar un PR existente: *"Usa el MCP de GitHub para revisar el PR
     #1 y dejar comentarios."*
4. Copia aqui abajo:
   - El comando/prompt exacto que usaste.
   - El link real al issue/commit/PR resultante.
   - Una captura de pantalla (opcional pero recomendable) en
     `evidence/screenshots/`.

## Registro (completar con tu evidencia real)

```
Fecha:
Accion realizada (issue / commit / PR):
Link:
Prompt usado en Claude Code:
```

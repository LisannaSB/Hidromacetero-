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

## Registro

Fecha: 9 de julio de 2026
Accion realizada: Issue creado
Link: https://github.com/LisannaSB/Hidromacetero-/issues/1
Prompt usado en Claude Code:
  "Usa el MCP de GitHub para crear un issue en el repositorio
  LisannaSB/Hidromacetero- titulado 'Agregar sensor capacitivo de
  suelo' con esta descripcion: El Dracal VCP-PTH450-CAL mide humedad
  relativa del aire, no humedad directa del sustrato/tierra. Para una
  medicion mas precisa de cuando regar, se recomendaria integrar un
  sensor capacitivo de suelo como entrada adicional, manteniendo la
  logica actual como fallback."

Conexion verificada con `claude mcp list` antes de ejecutar la accion:
  github: https://api.githubcopilot.com/mcp (HTTP) - ✔ Connected

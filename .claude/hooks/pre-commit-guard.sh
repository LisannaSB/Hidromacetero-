#!/usr/bin/env bash
#
# pre-commit-guard.sh
#
# Proposito: hook PreToolUse de Claude Code para HidroMacetero.
# Se ejecuta automaticamente ANTES de cualquier llamada a la herramienta
# Bash. Si detecta que el comando es un "git commit", revisa los archivos
# en staging (git diff --cached) y bloquea el commit si encuentra:
#   1. Un archivo .env real (no .env.example) a punto de subirse.
#   2. Patrones que parecen llaves/API keys/tokens hardcodeados.
#
# Esto existe porque este proyecto integra un sensor fisico y (a futuro)
# GitHub MCP: queremos evitar filtrar credenciales o configuraciones
# locales por accidente en un repositorio que ademas sera revisado como
# evidencia academica.
#
# Contrato de hooks de Claude Code: el script recibe por stdin un JSON
# con {"tool_name": "...", "tool_input": {...}, ...}. Si el script
# termina con exit code 2, Claude Code bloquea la ejecucion del tool y
# muestra stderr como retroalimentacion al modelo. Exit 0 = permitir.

set -euo pipefail

INPUT_JSON="$(cat)"

# Detectar cual interprete de Python hay disponible: en Windows suele
# existir solo "python", no "python3". Si no hay ninguno, no bloqueamos
# el comando (no podemos inspeccionarlo, pero preferimos no romper el
# flujo de trabajo del usuario por falta de una dependencia externa).
if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN=python3
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN=python
else
    exit 0
fi

# Extraer el comando de bash que se intenta ejecutar.
COMMAND=$(echo "$INPUT_JSON" | "$PYTHON_BIN" -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(data.get('tool_input', {}).get('command', ''))
except Exception:
    print('')
")

# Si el comando no es un git commit, no hay nada que revisar.
if [[ "$COMMAND" != *"git commit"* ]]; then
    exit 0
fi

# 1. Bloquear si hay un .env real (no .env.example) en staging.
STAGED_ENV_FILES=$(git diff --cached --name-only 2>/dev/null | grep -E '(^|/)\.env$' || true)
if [[ -n "$STAGED_ENV_FILES" ]]; then
    echo "BLOQUEADO: hay archivos .env en staging (posibles credenciales/config local):" >&2
    echo "$STAGED_ENV_FILES" >&2
    echo "Usa .env.example para valores de referencia y agrega .env a .gitignore." >&2
    exit 2
fi

# 2. Buscar patrones que parezcan llaves/tokens en el diff en staging.
SUSPICIOUS=$(git diff --cached 2>/dev/null | grep -E -i '(api[_-]?key|secret|token|password)\s*=\s*["'"'"'][A-Za-z0-9_\-]{12,}' || true)
if [[ -n "$SUSPICIOUS" ]]; then
    echo "BLOQUEADO: el diff en staging contiene texto que parece una credencial:" >&2
    echo "$SUSPICIOUS" >&2
    echo "Revisa el commit antes de continuar." >&2
    exit 2
fi

exit 0
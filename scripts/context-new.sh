#!/usr/bin/env bash

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

FIXTURES_DIR="$SCRIPT_DIR/fixtures"
CONTEXTS_DIR="$PROJECT_DIR/app/contexts"
ZIP_FILE="$FIXTURES_DIR/context_stub.zip"

echo -e "${PURPLE}${BOLD}Crear nuevo contexto${NC}"
echo

read -rp "$(echo -e "${CYAN}Nombre plural:${NC} ")" PLURAL_NAME
read -rp "$(echo -e "${CYAN}Nombre singular:${NC} ")" SINGULAR_NAME

if [[ -z "$PLURAL_NAME" || -z "$SINGULAR_NAME" ]]; then
    echo -e "${RED}Error: los nombres no pueden estar vacíos.${NC}"
    exit 1
fi

if [[ ! -f "$ZIP_FILE" ]]; then
    echo -e "${RED}Error: no existe:${NC} $ZIP_FILE"
    exit 1
fi

# Normalizar a minúsculas
ENTITY_NAME="$(printf '%s' "$SINGULAR_NAME" | tr '[:upper:]' '[:lower:]')"
ENTITY_PLURAL_NAME="$(printf '%s' "$PLURAL_NAME" | tr '[:upper:]' '[:lower:]')"

# Primera letra en mayúscula
ENTITY_CLASS="${ENTITY_NAME^}"
ENTITY_PLURAL_CLASS="${ENTITY_PLURAL_NAME^}"

TARGET_DIR="$CONTEXTS_DIR/$ENTITY_PLURAL_NAME"

if [[ -e "$TARGET_DIR" ]]; then
    echo -e "${RED}Error: ya existe:${NC} $TARGET_DIR"
    exit 1
fi

echo
echo -e "${YELLOW}→ Creando contexto...${NC}"

mkdir -p "$TARGET_DIR"

# El ZIP ya contiene directamente el contenido del contexto
unzip -q "$ZIP_FILE" -d "$TARGET_DIR"

echo -e "${YELLOW}→ Reemplazando placeholders...${NC}"

find "$TARGET_DIR" -type f -exec sed -i \
    -e "s/{EntityName}/$ENTITY_CLASS/g" \
    -e "s/{EntityPluralName}/$ENTITY_PLURAL_CLASS/g" \
    -e "s/{entity_name}/$ENTITY_NAME/g" \
    -e "s/{entity_plural_name}/$ENTITY_PLURAL_NAME/g" \
    {} +

echo
echo -e "${GREEN}${BOLD}✓ Contexto creado correctamente${NC}"
echo
echo -e "${CYAN}Ruta:${NC} $TARGET_DIR"
echo
echo -e "${PURPLE}${BOLD}Reemplazos:${NC}"
echo -e "  ${GREEN}{EntityName}${NC}          → $ENTITY_CLASS"
echo -e "  ${GREEN}{EntityPluralName}${NC}    → $ENTITY_PLURAL_CLASS"
echo -e "  ${GREEN}{entity_name}${NC}         → $ENTITY_NAME"
echo -e "  ${GREEN}{entity_plural_name}${NC}  → $ENTITY_PLURAL_NAME"
echo
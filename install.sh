#!/usr/bin/env bash
# ==============================================================================
# Script de instalação global ou local da SKILL 'add_reference' (AI Knowledge Librarian v2.0)
# ==============================================================================

set -e

# Configurações padrão
WORKSPACE=false
SKIP_DEPS=false
SKIP_TESTS=false
DRY_RUN=false
TARGET_DIR=""

usage() {
    echo "Uso: ./install.sh [opções]"
    echo ""
    echo "Opções:"
    echo "  -w, --workspace    Instala no workspace atual (.agents/skills/add_reference)"
    echo "  -d, --dir DIR      Define um diretório de destino customizado"
    echo "  -s, --skip-deps    Pula instalação de dependências Python"
    echo "  -t, --skip-tests   Pula a execução de testes pós-instalação"
    echo "  -n, --dry-run      Apenas simula a instalação sem fazer alterações"
    echo "  -h, --help         Exibe esta ajuda"
    exit 0
}

while [[ "$#" -gt 0 ]]; do
    case "$1" in
        -w|--workspace) WORKSPACE=true; shift ;;
        -d|--dir) TARGET_DIR="$2"; shift 2 ;;
        -s|--skip-deps) SKIP_DEPS=true; shift ;;
        -t|--skip-tests) SKIP_TESTS=true; shift ;;
        -n|--dry-run) DRY_RUN=true; shift ;;
        -h|--help) usage ;;
        *) echo "Opção desconhecida: $1"; usage ;;
    esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 1. Determina destino
if [ -z "$TARGET_DIR" ]; then
    if [ "$WORKSPACE" = true ]; then
        TARGET_DIR="$(pwd)/.agents/skills/add_reference"
    else
        TARGET_DIR="$HOME/.gemini/config/skills/add_reference"
    fi
fi

echo "============================================================"
echo " Instalação da SKILL: add_reference (AI Knowledge Librarian)"
echo "============================================================"
echo "[1/4] Destino da instalação: $TARGET_DIR"

if [ "$DRY_RUN" = true ]; then
    echo "[DRY-RUN] Simulação ativada. Nenhuma alteração física será realizada."
    echo "[DRY-RUN] Criaria diretório: $TARGET_DIR"
    echo "[DRY-RUN] Copiaria SKILL.md e pasta scripts/"
    if [ "$SKIP_DEPS" = false ]; then echo "[DRY-RUN] Executaria: pip install -r requirements.txt"; fi
    if [ "$SKIP_TESTS" = false ]; then echo "[DRY-RUN] Executaria suíte de testes unitários"; fi
    echo "Simulação concluída com sucesso!"
    exit 0
fi

# 2. Criação do diretório e cópia
mkdir -p "$TARGET_DIR"
mkdir -p "$TARGET_DIR/scripts"

cp "$SCRIPT_DIR/SKILL.md" "$TARGET_DIR/SKILL.md"
cp -r "$SCRIPT_DIR/scripts/"* "$TARGET_DIR/scripts/"
chmod +x "$TARGET_DIR/scripts/convert_to_md.py" || true

echo "  -> SKILL.md e scripts/ copiados com sucesso."

# 3. Dependências
echo "[2/4] Verificando dependências Python..."
if [ "$SKIP_DEPS" = false ]; then
    if command -v pip3 &>/dev/null; then
        PIP_CMD="pip3"
    elif command -v pip &>/dev/null; then
        PIP_CMD="pip"
    else
        PIP_CMD=""
    fi

    if [ -n "$PIP_CMD" ] && [ -f "$SCRIPT_DIR/requirements.txt" ]; then
        echo "  -> Instalando dependências recomendadas..."
        $PIP_CMD install -r "$SCRIPT_DIR/requirements.txt" -q || echo "Aviso: Falha ao instalar dependências via pip. Execute manualmente se necessário."
    fi
else
    echo "  -> Instalação de dependências pulada."
fi

# 4. Testes
echo "[3/4] Validando integridade..."
if [ "$SKIP_TESTS" = false ]; then
    if command -v python3 &>/dev/null; then
        PY_CMD="python3"
    else
        PY_CMD="python"
    fi

    echo "  -> Executando testes unitários..."
    $PY_CMD "$TARGET_DIR/scripts/test_convert_to_md.py"
    echo "  -> Todos os testes passaram com sucesso!"
else
    echo "  -> Execução de testes pulada."
fi

# 5. Finalização
echo "[4/4] Finalização e Prontidão"
echo ""
echo "✓ SKILL 'add_reference' instalada com sucesso!"
echo ""
echo "Como utilizar:"
echo "1. No Antigravity / Gemini CLI, invoque com: /add_reference"
echo "2. Ou solicite em linguagem natural: 'Adicione o documento X como referência'"
echo "3. Para busca cirúrgica via terminal:"
echo "   python3 \"$TARGET_DIR/scripts/convert_to_md.py\" --query \"<termo>\" \"<workspace>/.referencias\""
echo ""

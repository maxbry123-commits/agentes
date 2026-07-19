#!/bin/bash
# deploy_vps.sh — Sube los documentos del orquestador a una carpeta fija del VPS
# Uso: bash deploy_vps.sh usuario@vps-ip
# Resultado: /opt/orquestador-universal/ en el VPS con todos los docs

set -e

VPS="${1:?Uso: bash deploy_vps.sh usuario@ip-vps}"
DEST="/opt/orquestador-universal"

echo "============================================================"
echo "  Desplegando orquestador en: $VPS"
echo "  Destino: $DEST"
echo "============================================================"

# 1. Crear carpeta remota
echo "[1/4] Creando carpeta en VPS..."
ssh "$VPS" "sudo mkdir -p $DEST && sudo chown \$USER:\$USER $DEST"

# 2. Subir todos los archivos del orquestador
echo "[2/4] Subiendo archivos..."
LOCAL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
scp -r "$LOCAL_DIR"/* "$VPS:$DEST/"

# 3. Hacer ejecutables los scripts
echo "[3/4] Configurando permisos..."
ssh "$VPS" "chmod +x $DEST/setup.sh $DEST/deploy_vps.sh $DEST/main_dsl.py $DEST/main_runtime.py $DEST/main.py 2>/dev/null || true"

# 4. Verificar
echo "[4/4] Verificando instalación..."
ssh "$VPS" "ls $DEST | head -20"
echo ""
echo "============================================================"
echo "  ✓ Listo. Para arrancar:"
echo "  ssh $VPS"
echo "  cd $DEST"
echo "  python3 main_runtime.py --demo"
echo "============================================================"

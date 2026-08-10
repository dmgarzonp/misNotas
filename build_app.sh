#!/usr/bin/env bash
# Script de empaquetado autónomo para Mis Apuntes en Ubuntu Linux

set -e

echo "📦 Iniciando empaquetado de Mis Apuntes..."

# Instalar PyInstaller en el entorno virtual si no está instalado
.venv/bin/pip install --quiet pyinstaller

# Generar ejecutable binario autónomo
.venv/bin/pyinstaller --noconfirm --onedir --windowed \
    --name "MisApuntes" \
    --add-data "skills:skills" \
    main.py

echo "✅ Ejecutable generado exitosamente en: dist/MisApuntes/MisApuntes"

# Crear lanzador de escritorio (.desktop) en ~/.local/share/applications/
DESKTOP_FILE="$HOME/.local/share/applications/mis-apuntes.desktop"
APP_DIR="$(pwd)"

cat <<EOF > "$DESKTOP_FILE"
[Desktop Entry]
Version=1.0
Type=Application
Name=Mis Apuntes
Comment=Aplicación de Notas Rápidas Premium estilo macOS Sequoia para Ubuntu
Exec=$APP_DIR/dist/MisApuntes/MisApuntes
Icon=accessories-text-editor
Terminal=false
Categories=Utility;Application;
EOF

chmod +x "$DESKTOP_FILE"

echo "🎉 Lanzador de escritorio creado en: $DESKTOP_FILE"
echo "Ahora puedes buscar 'Mis Apuntes' directamente en el menú de aplicaciones de Ubuntu."

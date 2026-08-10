#!/usr/bin/env bash

# Exit on error
set -e

VERSION="1.0.0"
APP_NAME="mis-apuntes"
DEB_DIR="build/deb/${APP_NAME}_${VERSION}_amd64"

echo "=== 🚀 Iniciando compilación y empaquetado de Mis Apuntes v${VERSION} ==="

# 1. Ensure PyInstaller is installed in virtualenv
if ! .venv/bin/python -c "import PyInstaller" 2>/dev/null; then
    echo "📦 Instalando PyInstaller..."
    .venv/bin/pip install pyinstaller
fi

# 2. Build standalone binary using PyInstaller
echo "🛠️ Compilando ejecutable con PyInstaller..."
.venv/bin/pyinstaller --noconfirm MisApuntes.spec

# 3. Create Debian Package Structure
echo "📦 Construyendo estructura del paquete .deb..."
rm -rf "build/deb"
mkdir -p "${DEB_DIR}/DEBIAN"
mkdir -p "${DEB_DIR}/usr/bin"
mkdir -p "${DEB_DIR}/usr/share/applications"

# Control File
cat <<EOF > "${DEB_DIR}/DEBIAN/control"
Package: ${APP_NAME}
Version: ${VERSION}
Architecture: amd64
Maintainer: Diego Garzón <dmgarzonp@gmail.com>
Description: Aplicación de Notas Rápidas y Notas de Escritorio Persistentes para Ubuntu.
 Apple Notes macOS Sequoia & Ubuntu GNOME aesthetics, Math Notes y SQLite WAL mode.
EOF

# Copy compiled PyInstaller dist to /usr/bin/mis-apuntes
cp -r dist/MisApuntes/* "${DEB_DIR}/usr/bin/"
chmod +x "${DEB_DIR}/usr/bin/MisApuntes"

# Desktop File
cat <<EOF > "${DEB_DIR}/usr/share/applications/mis-apuntes.desktop"
[Desktop Entry]
Type=Application
Name=Mis Apuntes
Comment=Notas Rápidas y Notas de Escritorio Persistentes
Exec=/usr/bin/MisApuntes
Icon=text-x-generic
Terminal=false
Categories=Utility;Application;
StartupNotify=false
EOF

# 4. Build .deb package
echo "🔨 Generando paquete .deb en dist/${APP_NAME}_${VERSION}_amd64.deb..."
dpkg-deb --build "${DEB_DIR}" "dist/${APP_NAME}_${VERSION}_amd64.deb"

echo "✅ Empaquetado completado con éxito."
echo " Archivos en dist/:"
ls -lh dist/

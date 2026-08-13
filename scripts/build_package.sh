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
mkdir -p "${DEB_DIR}/usr/lib/mis-apuntes"
mkdir -p "${DEB_DIR}/usr/share/applications"
mkdir -p "${DEB_DIR}/usr/share/icons/hicolor/scalable/apps"

# Control File
cat <<EOF > "${DEB_DIR}/DEBIAN/control"
Package: ${APP_NAME}
Version: ${VERSION}
Architecture: amd64
Maintainer: Diego Garzón <dmgarzonp@gmail.com>
Depends: libxcb-cursor0, libgl1, libegl1, libdbus-1-3, libxkbcommon-x11-0, libx11-xcb1, libfontconfig1, libfreetype6, pkexec, gnome-shell-extension-appindicator
Description: Aplicación de Notas Rápidas y Notas de Escritorio Persistentes para Ubuntu.
 Apple Notes macOS Sequoia & Ubuntu GNOME aesthetics, Math Notes y SQLite WAL mode.
EOF


# Post-install Script
cat <<EOF > "${DEB_DIR}/DEBIAN/postinst"
#!/bin/sh
set -e
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database -q || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor || true
fi
EOF
chmod +x "${DEB_DIR}/DEBIAN/postinst"

# Post-remove Script
cat <<EOF > "${DEB_DIR}/DEBIAN/postrm"
#!/bin/sh
set -e
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database -q || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor || true
fi
EOF
chmod +x "${DEB_DIR}/DEBIAN/postrm"

# Copy compiled PyInstaller dist to /usr/lib/mis-apuntes/
cp -r dist/MisApuntes/* "${DEB_DIR}/usr/lib/mis-apuntes/"
chmod +x "${DEB_DIR}/usr/lib/mis-apuntes/MisApuntes"

# Create symlinks in /usr/bin for terminal execution
ln -sf /usr/lib/mis-apuntes/MisApuntes "${DEB_DIR}/usr/bin/mis-apuntes"
ln -sf /usr/lib/mis-apuntes/MisApuntes "${DEB_DIR}/usr/bin/MisApuntes"

# Copy Application Icon
cp data/mis-apuntes.svg "${DEB_DIR}/usr/share/icons/hicolor/scalable/apps/mis-apuntes.svg"

# Desktop Entry File
cat <<EOF > "${DEB_DIR}/usr/share/applications/mis-apuntes.desktop"
[Desktop Entry]
Type=Application
Name=Mis Apuntes
Comment=Notas Rápidas y Notas de Escritorio Persistentes
Exec=/usr/lib/mis-apuntes/MisApuntes
Icon=mis-apuntes
Terminal=false
Categories=Utility;Application;
StartupNotify=false
EOF

# 4. Build .deb package
echo "🔨 Generando paquete .deb en dist/${APP_NAME}_${VERSION}_amd64.deb..."
dpkg-deb --build --root-owner-group "${DEB_DIR}" "dist/${APP_NAME}_${VERSION}_amd64.deb"
chmod 644 "dist/${APP_NAME}_${VERSION}_amd64.deb"

echo "✅ Empaquetado completado con éxito."
echo "Archivos en dist/:"
ls -lh dist/

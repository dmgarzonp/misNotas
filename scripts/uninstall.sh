#!/usr/bin/env bash
# Script de desinstalación completa para Mis Apuntes en Ubuntu Linux

set -e

echo "=== 🗑️ Iniciando desinstalación completa de Mis Apuntes ==="

if [ "$EUID" -ne 0 ]; then
    echo "🔑 Solicitando permisos de superusuario (sudo)..."
    SUDO="sudo"
else
    SUDO=""
fi

# 1. Detener servicio de usuario en systemd si está activo
if command -v systemctl >/dev/null 2>&1; then
    echo "⏹️ Deteniendo servicios de usuario..."
    systemctl --user stop mis-apuntes.service 2>/dev/null || true
    systemctl --user disable mis-apuntes.service 2>/dev/null || true
fi

# 2. Desinstalar paquete Debian con apt o dpkg
echo "📦 Removiendo paquete mis-apuntes del sistema..."
if dpkg -l mis-apuntes 2>/dev/null | grep -q "^ii"; then
    $SUDO apt-get purge -y mis-apuntes 2>/dev/null || $SUDO dpkg -P mis-apuntes 2>/dev/null || true
fi

# 3. Eliminar posibles binarios residuales en el sistema
echo "🧹 Limpiando binarios e iconos globales..."
$SUDO rm -rf /usr/bin/MisApuntes /usr/bin/mis-apuntes /usr/bin/_internal /usr/lib/mis-apuntes
$SUDO rm -f /usr/share/applications/mis-apuntes.desktop
$SUDO rm -f /usr/share/icons/hicolor/scalable/apps/mis-apuntes.svg

# 4. Eliminar autostart y datos de usuario
echo "🏠 Limpiando configuraciones y base de datos del usuario..."
rm -f "$HOME/.config/autostart/mis-apuntes.desktop"
rm -f "$HOME/.config/systemd/user/mis-apuntes.service"
rm -rf "$HOME/.local/share/misNotas"

# 5. Refrescar cachés de iconos y aplicaciones
if command -v update-desktop-database >/dev/null 2>&1; then
    $SUDO update-desktop-database -q || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    $SUDO gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor || true
fi

echo "✨ Desinstalación completada. Se eliminaron todos los componentes de Mis Apuntes del sistema operativo."

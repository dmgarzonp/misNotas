#!/usr/bin/env bash
# Script para instalar dependencias de sistema necesarias para Mis Apuntes en Ubuntu/Debian

set -e

echo "=== 📦 Instalando dependencias del sistema para Mis Apuntes ==="

if [ "$EUID" -ne 0 ]; then
    echo "🔑 Solicitando permisos de superusuario (sudo)..."
    SUDO="sudo"
else
    SUDO=""
fi

$SUDO apt-get update -qq

DEPENDENCIES=(
    libxcb-cursor0
    libgl1
    libegl1
    libdbus-1-3
    libxkbcommon-x11-0
    libx11-xcb1
    libfontconfig1
    libfreetype6
    pkexec
    policykit-1-gnome
    gnome-shell-extension-appindicator
)

echo "🛠️ Instalando librerías Qt6 y XCB..."
$SUDO apt-get install -y "${DEPENDENCIES[@]}"

echo "✅ Dependencias instaladas con éxito."
echo "Ahora puedes ejecutar la aplicación con: mis-apuntes o /usr/bin/MisApuntes"

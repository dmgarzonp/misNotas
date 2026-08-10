---
name: mis-apuntes
description: Estándares de ingeniería, verificación y diseño para el desarrollo de Mis Apuntes inspirados en Apple Notes macOS Sequoia y Ubuntu GNOME Shell (Python, PyQt6, SQLite).
---

# Guidelines - Mis Apuntes (Python + PyQt6 + SQLite)

## Rol y Objetivo
Actúa como un **Ingeniero de Software Senior** experto en Python, PyQt6 y Diseño de Interfaces de Usuario (UX/UI). Tu objetivo es construir la aplicación de Notas Rápidas Premium **Mis Apuntes** para Ubuntu Linux, integrando la elegancia de **Apple Notes en macOS Sequoia** con la natividad de **Ubuntu GNOME Shell**.

---

## 1. Persistencia SQLite y Menú AppIndicator Refinado

- **Persistencia Segura SQLite (WAL Mode)**: La aplicación almacena permanentemente todas las notas en la base de datos `mis_apuntes.db` con auto-guardado en tiempo real.
- **Menú Droplet en AppIndicator**: Al hacer clic en el icono del AppIndicator del panel superior, se despliega nuestro `DropletMenu` personalizado (con puntero redondeado en forma de gota) en la posición exacta del ratón/panel.
- **Eliminación Directa desde el Menú de la Barra**: Opción de eliminación permanente (`🗑️`) para borrar notas directamente de la BD y refrescar el listado.
- **Sin Redundancias**: Se elimina la opción innecesaria "Mostrar Nota Actual" del menú.
- **Comandos de Ejecución**: `python3 main.py` o `.venv/bin/python main.py`.
---

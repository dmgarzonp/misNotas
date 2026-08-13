# 📦 Guía Completa: Publicación de Mis Apuntes en Flatpak y Flathub (Tienda Oficial Ubuntu / GNOME)

Esta guía explica en detalle cómo empaquetar, probar localmente y publicar **Mis Apuntes** en **Flathub**, la fuente oficial de paquetes Flatpak adoptada por Ubuntu Software (Centro de Aplicaciones) y GNOME Software.

---

## 1. Requisitos Previos

Asegúrate de tener instaladas las herramientas de construcción de Flatpak en Ubuntu:

```bash
sudo apt update
sudo apt install -y flatpak flatpak-builder gnome-software-plugin-flatpak
flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
```

Instala el SDK y runtime de GNOME 47:

```bash
flatpak install flathub org.gnome.Platform//47 org.gnome.Sdk//47
```

---

## 2. Estructura de Archivos Creados

En el repositorio se encuentran los archivos necesarios en el directorio `flatpak/`:

1. **`flatpak/org.misapuntes.MisApuntes.yml`**: Manifiesto de construcción de Flatpak con permisos de pantalla X11/Wayland, bandeja del sistema y persistencia SQLite.
2. **`flatpak/org.misapuntes.MisApuntes.desktop`**: Lanzador de escritorio adaptado al ID de Flatpak (`org.misapuntes.MisApuntes`).
3. **`flatpak/org.misapuntes.MisApuntes.appdata.xml`**: Metadatos AppStream requeridos por la Tienda de Ubuntu y GNOME Software (descripciones, capturas, licencias y enlaces).

---

## 3. Compilación y Prueba Local

Para probar el paquete Flatpak en tu computador antes de enviarlo a la tienda:

```bash
# 1. Crear el directorio de construcción y compilar
flatpak-builder --force-clean build-dir flatpak/org.misapuntes.MisApuntes.yml

# 2. Instalar el paquete compilado localmente
flatpak-builder --user --install --force-clean build-dir flatpak/org.misapuntes.MisApuntes.yml

# 3. Ejecutar la aplicación desde Flatpak
flatpak run org.misapuntes.MisApuntes
```

Para validar los metadatos y el manifiesto con las reglas oficiales de Flathub:

```bash
pip install flatpak-builder-lint
flatpak-builder-lint appstream flatpak/org.misapuntes.MisApuntes.appdata.xml
flatpak-builder-lint manifest flatpak/org.misapuntes.MisApuntes.yml
```

---

## 4. Proceso de Publicación en Flathub (Tienda Oficial)

Flathub es el repositorio oficial que alimenta la tienda de Ubuntu y GNOME Software. El proceso de envío se realiza mediante un Pull Request en GitHub:

### Paso 1: Subir tu Código a GitHub
Asegúrate de que tu repositorio en GitHub (ej. `https://github.com/dmgarzonp/misNotas`) sea público y contenga los cambios actuales.

### Paso 2: Bifurcar (Fork) el Repositorio de Flathub
1. Entra a: [https://github.com/flathub/flathub](https://github.com/flathub/flathub)
2. Haz clic en **Fork** (arriba a la derecha) para crear una copia en tu cuenta de GitHub.

### Paso 3: Crear una Nueva Rama y Subir el Manifiesto
Clona tu fork localmente y crea una rama con el nombre de tu App ID:

```bash
git clone https://github.com/tu-usuario/flathub.git
cd flathub
git checkout -b org.misapuntes.MisApuntes
```

Copia `flatpak/org.misapuntes.MisApuntes.yml` dentro del repositorio `flathub` y haz commit:

```bash
cp /ruta/a/misNotas/flatpak/org.misapuntes.MisApuntes.yml .
git add org.misapuntes.MisApuntes.yml
git commit -m "Add org.misapuntes.MisApuntes"
git push origin org.misapuntes.MisApuntes
```

### Paso 4: Crear el Pull Request en GitHub
1. Ve a `https://github.com/flathub/flathub` y abre un **Pull Request** desde tu rama `org.misapuntes.MisApuntes`.
2. El bot automático de Flathub (`flathubbot`) compilará la aplicación automáticamente para arquitectura `x86_64` y `aarch64`.
3. Un revisor de Flathub aprobará la solicitud.

### Paso 5: Publicación Final
Una vez aprobado el Pull Request:
- Flathub creará el repositorio dedicado `https://github.com/flathub/org.misapuntes.MisApuntes`.
- La aplicación aparecerá en [flathub.org](https://flathub.org) y en la **Tienda Oficial de Ubuntu / GNOME Software** para millones de usuarios.

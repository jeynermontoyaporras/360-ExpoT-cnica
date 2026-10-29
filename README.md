# Expo Técnica Regional 2026 · Vista 360°

Visor panorámico de la Expo Técnica Regional del CORVEC Pacífico Central, con 17 estands y 20 fotografías vinculadas.

## Abrir el proyecto

Abre `Proyecto/sitio/index.html` en un navegador con WebGL. También puedes ejecutar `python -m http.server 8000` desde `Proyecto/sitio` y visitar `http://localhost:8000`.

## Archivos

- `Proyecto/sitio/`: visor, estilos, fotografías y panorámica actual.
- `Proyecto/sitio/stands.js`: títulos, galerías y posiciones de los botones sobre la esfera.
- `Proyecto/originales/`: fotografías DJI originales.
- `Proyecto/procesamiento/`: scripts y referencias de reconstrucción.
- `Proyecto/configuracion/hosting.json`: identificación del sitio publicado en Sites.
- `agregar_*.py` y `ubicar.py`: scripts históricos para ubicar estands a partir de capturas; contienen rutas y supuestos que deben revisarse antes de reutilizarlos.

## Publicación

Sitio público: https://expo-esparza-panorama-360.jeynermmp.chatgpt.site

Guardar cambios en GitHub no publica automáticamente en Sites. La publicación se realiza por separado usando el identificador conservado en la configuración.

Consulta `Proyecto/LEEME.txt` para detalles del visor y del procesamiento original.

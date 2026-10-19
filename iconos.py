"""Íconos vectoriales de la interfaz (SVG de línea) y rutas de recursos.

Los íconos son SVG sencillos dibujados con trazo, que se pintan del color que se
pida (guinda sobre fondo claro, blanco sobre fondo guinda). Así no hace falta
tener archivos de imagen sueltos para cada botón.

Las rutas funcionan igual al ejecutar con `python main_gui.py` que dentro del
ejecutable creado con PyInstaller.
"""
import sys
from pathlib import Path

# Cuerpo de cada ícono, en una cuadrícula de 24 x 24
CUERPOS = {
    # Catálogos
    "Paciente": '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
    "Medico": '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>'
              '<line x1="19" y1="8" x2="19" y2="14"/><line x1="16" y1="11" x2="22" y2="11"/>',
    "Consultorio": '<path d="M3 21V9l9-6 9 6v12z"/><path d="M9 21v-7h6v7"/>',
    "Padecimiento": '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>',
    "Rol": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
    "Permiso": '<rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
    # Acciones
    "insertar": '<line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>',
    "actualizar": '<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/>',
    "eliminar": '<path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="M6 6l1 14h10l1-14"/>'
                '<line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/>',
    "consultar": '<circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>',
    "todos": '<line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/>'
             '<line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/>'
             '<line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/>',
}


def svg(nombre, color, grosor=2):
    """Texto SVG del ícono con el color indicado."""
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
        f'stroke="{color}" stroke-width="{grosor}" stroke-linecap="round" stroke-linejoin="round">'
        f"{CUERPOS[nombre]}</svg>"
    )


def pixmap(nombre, color, tam=24, grosor=2):
    """Dibuja el ícono en un QPixmap nítido (al doble de resolución)."""
    from PyQt6.QtCore import QByteArray, QRectF, Qt
    from PyQt6.QtGui import QPainter, QPixmap
    from PyQt6.QtSvg import QSvgRenderer

    escala = 2
    imagen = QPixmap(tam * escala, tam * escala)
    imagen.fill(Qt.GlobalColor.transparent)
    render = QSvgRenderer(QByteArray(svg(nombre, color, grosor).encode("utf-8")))
    pintor = QPainter(imagen)
    render.render(pintor, QRectF(0, 0, tam * escala, tam * escala))
    pintor.end()
    imagen.setDevicePixelRatio(escala)
    return imagen


def icono(nombre, color, tam=24, grosor=2):
    from PyQt6.QtGui import QIcon

    return QIcon(pixmap(nombre, color, tam, grosor))


# ---- Rutas de recursos -------------------------------------------------
def carpeta_app():
    """Carpeta donde está el programa (o el .exe). Aquí van el .env y las imágenes propias."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


def carpeta_interna():
    """Carpeta de los recursos empaquetados dentro del ejecutable."""
    return Path(getattr(sys, "_MEIPASS", carpeta_app()))


def buscar(relativa):
    """Ruta de un recurso. Primero busca junto al programa (para que puedas reemplazarlo
    con tu propia imagen) y luego dentro del paquete. Regresa None si no existe."""
    for base in (carpeta_app(), carpeta_interna()):
        ruta = base / relativa
        if ruta.exists():
            return ruta
    return None

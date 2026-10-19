"""Identidad gráfica del Gobierno del Estado de Michoacán aplicada a la app.

Referencia: https://michoacan.gob.mx/guia-grafica/

Lo que toma de la guía:
  - Texto sobre fondo blanco en guinda #4A001F.
  - Sobre fondo guinda, el texto va en blanco #FFFFFF o rosa claro #FFC4D0.
  - Encabezado con el logotipo oficial arriba a la izquierda (máximo 85 px de alto),
    tomado SIEMPRE del CDN oficial y con una pleca inferior rosa de 5 px.
  - Tipografía oficial Gibson; texto de cuerpo de 18 px.
  - Pie de página en guinda.

Los recursos (logotipo, favicon y fuente) se leen del CDN al abrir la app y no se
guardan en el disco. Si no hay internet, la app funciona igual con un encabezado
de texto y una tipografía alterna.

Nota: la guía menciona también un morado y un gris, pero no publica sus códigos
hexadecimales; por eso la app solo usa guinda, rosa claro y blanco.
"""
import urllib.request

from PyQt6.QtCore import QByteArray, QRectF, Qt
from PyQt6.QtGui import QFontDatabase, QIcon, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer

from iconos import buscar

# ---- Colores oficiales ------------------------------------------------
GUINDA = "#4A001F"
ROSA_CLARO = "#FFC4D0"
BLANCO = "#FFFFFF"
ROSA_PLECA = "#FFC3D0"   # el que usa la guía en el borde inferior del encabezado
ROSA_FILA = "#FFF4F7"    # tinte muy suave del rosa, solo para filas alternas de la tabla

# ---- Recursos del CDN oficial ----------------------------------------
CDN = "https://michoacan.gob.mx/cdn/"
URL_LOGO = CDN + "img/logo.svg"
URL_FAVICON = CDN + "img/favicon/favicon.ico"
URL_FUENTE = CDN + "fonts/gibson-regular-webfont.woff"

ALTO_LOGO = 85           # máximo permitido por la guía
TEXTO_PX = 18            # tamaño del cuerpo de texto según la guía
TABLA_PX = 16            # las tablas usan un poco menos para que quepan sus columnas

FUENTES = '"Gibson", "Segoe UI", "Helvetica Neue", Arial, sans-serif'

_sin_red = False         # si falla una descarga, no se insiste con las demás


def descargar(url, tiempo=3):
    """Regresa los bytes de la URL o None si no se pudo (sin internet, bloqueo, etc.)."""
    global _sin_red
    if _sin_red:
        return None
    try:
        peticion = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(peticion, timeout=tiempo) as respuesta:
            return respuesta.read()
    except Exception:
        _sin_red = True
        return None


def cargar_fuente():
    """Registra la fuente Gibson. Primero busca archivos en la carpeta 'fuentes' y
    luego la descarga del CDN. Regresa True si Gibson quedó disponible."""
    carpeta = buscar("fuentes")
    if carpeta is not None:
        for ruta in sorted(carpeta.iterdir()):
            if ruta.suffix.lower() in (".ttf", ".otf") and ruta.name.lower().startswith("gibson"):
                QFontDatabase.addApplicationFont(str(ruta))
    if "Gibson" not in QFontDatabase.families():
        datos = descargar(URL_FUENTE)
        if datos:
            QFontDatabase.addApplicationFontFromData(QByteArray(datos))
    return "Gibson" in QFontDatabase.families()


def cargar_logo(alto=ALTO_LOGO):
    """Descarga el logotipo oficial (SVG) y lo dibuja con el alto indicado."""
    datos = descargar(URL_LOGO)
    if not datos:
        return None
    render = QSvgRenderer(QByteArray(datos))
    tam = render.defaultSize()
    if not render.isValid() or tam.height() <= 0:
        return None
    ancho = round(tam.width() * alto / tam.height())
    escala = 2  # se dibuja al doble para que se vea nítido en pantallas de alta densidad
    imagen = QPixmap(ancho * escala, alto * escala)
    imagen.fill(Qt.GlobalColor.transparent)
    pintor = QPainter(imagen)
    render.render(pintor, QRectF(0, 0, ancho * escala, alto * escala))
    pintor.end()
    imagen.setDevicePixelRatio(escala)
    return imagen


def cargar_icono():
    """Favicon oficial para la ventana. Regresa un QIcon (vacío si no se pudo)."""
    datos = descargar(URL_FAVICON)
    imagen = QPixmap()
    if datos and imagen.loadFromData(datos):
        return QIcon(imagen)
    local = buscar("imagenes/icono.ico")   # ícono propio si no hay internet
    return QIcon(str(local)) if local else QIcon()


def hoja_de_estilo():
    """Hoja de estilo (QSS) de toda la aplicación."""
    return f"""
* {{
    font-family: {FUENTES};
    font-size: {TEXTO_PX}px;
    color: {GUINDA};
}}
QMainWindow, QDialog, QMessageBox, QWidget#contenido {{
    background: {BLANCO};
}}

/* Encabezado: logo a la izquierda, menú a la derecha, pleca rosa de 5 px */
QWidget#encabezado {{
    background: {BLANCO};
    border-bottom: 5px solid {ROSA_PLECA};
}}
QMenuBar {{
    background: transparent;
    color: {GUINDA};
}}
QMenuBar::item {{
    padding: 10px 18px;
    background: transparent;
    border-radius: 4px;
}}
QMenuBar::item:selected {{
    background: {ROSA_CLARO};
    color: {GUINDA};
}}
QMenu {{
    background: {BLANCO};
    border: 1px solid {ROSA_CLARO};
    padding: 4px;
}}
QMenu::item {{
    padding: 8px 30px;
}}
QMenu::item:selected {{
    background: {ROSA_CLARO};
    color: {GUINDA};
}}

/* Textos */
QLabel#titulo {{
    font-size: 30px;
    font-weight: bold;
}}
QLabel#subtitulo {{
    font-size: {TEXTO_PX}px;
}}
QLabel#seccion {{
    font-size: 22px;
    font-weight: bold;
}}
QLabel#etiqueta_icono {{
    background: {ROSA_CLARO};
    border-radius: 28px;
}}
QLabel#vacio {{
    font-size: {TEXTO_PX}px;
    background: {ROSA_FILA};
    border: 2px dashed {ROSA_CLARO};
    border-radius: 12px;
    padding: 18px;
}}
QLabel#error {{
    background: {ROSA_CLARO};
    color: {GUINDA};
    border-radius: 6px;
    padding: 8px 12px;
}}

/* Botones: el principal va relleno de guinda; los demás con borde guinda */
QPushButton {{
    background: {BLANCO};
    color: {GUINDA};
    border: 2px solid {GUINDA};
    border-radius: 22px;
    padding: 9px 24px;
    font-weight: bold;
}}
QPushButton:hover {{
    background: {ROSA_CLARO};
}}
QPushButton#primario {{
    background: {GUINDA};
    color: {BLANCO};
}}
QPushButton#primario:hover {{
    background: {GUINDA};
    color: {BLANCO};
    border: 2px solid {ROSA_CLARO};
}}

/* Tarjetas de la pantalla de inicio */
QFrame#tarjeta {{
    background: {BLANCO};
    border: 2px solid {ROSA_CLARO};
    border-radius: 16px;
}}
QFrame#tarjeta:hover {{
    background: {ROSA_FILA};
    border: 2px solid {GUINDA};
}}
QLabel#tarjeta_titulo {{
    font-size: 21px;
    font-weight: bold;
    background: transparent;
}}
QLabel#tarjeta_conteo {{
    font-size: {TABLA_PX}px;
    background: transparent;
}}

/* Campos de captura */
QLineEdit, QComboBox, QDateEdit {{
    background: {BLANCO};
    border: 2px solid {ROSA_CLARO};
    border-radius: 10px;
    padding: 8px 10px;
    selection-background-color: {GUINDA};
    selection-color: {BLANCO};
}}
QLineEdit:focus, QComboBox:focus, QDateEdit:focus {{
    border-color: {GUINDA};
}}
QComboBox QAbstractItemView {{
    background: {BLANCO};
    selection-background-color: {ROSA_CLARO};
    selection-color: {GUINDA};
}}

/* Tablas: encabezado guinda con texto blanco */
QTableWidget {{
    font-size: {TABLA_PX}px;
    background: {BLANCO};
    alternate-background-color: {ROSA_FILA};
    border: 1px solid {ROSA_CLARO};
    gridline-color: {ROSA_CLARO};
    selection-background-color: {ROSA_CLARO};
    selection-color: {GUINDA};
}}
QHeaderView::section {{
    background: {GUINDA};
    color: {BLANCO};
    font-size: {TABLA_PX}px;
    font-weight: bold;
    padding: 8px;
    border: none;
}}

/* Pie de página guinda con texto blanco */
QStatusBar {{
    background: {GUINDA};
    color: {BLANCO};
}}
QStatusBar QLabel {{
    color: {BLANCO};
    padding: 2px 10px;
}}
"""

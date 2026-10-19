"""Aplicación de escritorio · Sistema de gestión de citas médicas (Centro de Salud de Villamar).

Ejecutar con:  python main_gui.py

Menú principal:
    Inicio
    Catálogos  -> Pacientes, Médicos, Consultorios, Padecimientos, Roles, Permisos
                  (cada uno abre su CRUD: Insertar, Actualizar, Eliminar, Consultar)
    Base de datos -> SQL Server / PostgreSQL
    Ayuda -> Acerca de
"""
import io
import os
import sys
from contextlib import redirect_stdout

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QActionGroup, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenuBar,
    QMessageBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

import tema
from iconos import buscar, carpeta_app
from menu import Menu
from repositorio import ErrorBD, RepositorioCatalogo
from ventanas import ETIQUETAS, CatalogoWidget, InicioWidget, aviso

MOTORES = ("SQL Server", "PostgreSQL")


class VentanaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de gestión de citas · Centro de Salud de Villamar")
        self.setWindowIcon(tema.cargar_icono())
        self.resize(1320, 780)
        self.setMinimumSize(1100, 680)

        self.conexion = None     # objeto ConexionSQLServer o ConexionPostgresql
        self.marcador = None     # "?" o "%s"
        self.motor = None        # "SQL Server" o "PostgreSQL"
        self.catalogos = {}      # clave de Menu.TABLAS -> CatalogoWidget (ya creados)

        contenido = QWidget()
        contenido.setObjectName("contenido")
        capa = QVBoxLayout(contenido)
        capa.setContentsMargins(0, 0, 0, 0)
        capa.setSpacing(0)
        capa.addWidget(self._crear_encabezado())

        self.pila = QStackedWidget()
        self.inicio = InicioWidget()
        self.inicio.abrir.connect(self.abrir_catalogo)   # clic en una tarjeta de la pantalla de inicio
        self.pila.addWidget(self.inicio)
        capa.addWidget(self.pila, 1)
        self.setCentralWidget(contenido)

        self._crear_pie()
        self._mostrar_estado_conexion()

    # ------------------------------------------------------------------
    # Encabezado: logotipo oficial a la izquierda y menú a la derecha
    # ------------------------------------------------------------------
    def _crear_encabezado(self):
        encabezado = QWidget()
        encabezado.setObjectName("encabezado")
        fila = QHBoxLayout(encabezado)
        fila.setContentsMargins(24, 8, 24, 8)

        logo = QLabel()
        imagen = tema.cargar_logo()
        if imagen is not None:
            logo.setPixmap(imagen)
        else:  # sin internet: encabezado de texto
            logo.setText("GOBIERNO DEL ESTADO\nDE MICHOACÁN")
            logo.setObjectName("titulo")
        fila.addWidget(logo)

        # Logotipo de la dependencia (opcional): guarda el archivo como imagenes/logo_salud.png
        ruta_salud = None
        for nombre in ("logo_salud.png", "logo_salud.jpg", "logo_salud.jpeg"):
            ruta_salud = buscar("imagenes/" + nombre)
            if ruta_salud:
                break
        if ruta_salud:
            imagen_salud = QPixmap(str(ruta_salud))
            if not imagen_salud.isNull():
                imagen_salud = imagen_salud.scaledToHeight(112, Qt.TransformationMode.SmoothTransformation)
                imagen_salud.setDevicePixelRatio(2)   # 56 px de alto en pantalla, nítido
                separador = QFrame()
                separador.setFixedSize(2, 56)
                separador.setStyleSheet(f"background: {tema.ROSA_PLECA};")
                logo_salud = QLabel()
                logo_salud.setPixmap(imagen_salud)
                fila.addSpacing(16)
                fila.addWidget(separador)
                fila.addSpacing(16)
                fila.addWidget(logo_salud)
        fila.addStretch()

        barra = QMenuBar()
        fila.addWidget(barra)

        accion_inicio = QAction("Inicio", self)
        accion_inicio.triggered.connect(self.mostrar_inicio)
        barra.addAction(accion_inicio)

        self.menu_catalogos = barra.addMenu("Catálogos")
        for clave, tabla in Menu.TABLAS.items():
            accion = QAction(ETIQUETAS[tabla["nombre"]], self)
            accion.triggered.connect(lambda checked=False, c=clave: self.abrir_catalogo(c))
            self.menu_catalogos.addAction(accion)

        menu_bd = barra.addMenu("Base de datos")
        grupo = QActionGroup(self)
        grupo.setExclusive(True)
        self.acciones_motor = {}
        for motor in MOTORES:
            accion = QAction(motor, self)
            accion.setCheckable(True)
            accion.triggered.connect(lambda checked=False, m=motor: self.cambiar_motor(m))
            grupo.addAction(accion)
            menu_bd.addAction(accion)
            self.acciones_motor[motor] = accion

        menu_ayuda = barra.addMenu("Ayuda")
        accion_acerca = QAction("Acerca de", self)
        accion_acerca.triggered.connect(self.acerca_de)
        menu_ayuda.addAction(accion_acerca)
        return encabezado

    # ------------------------------------------------------------------
    # Pie de página guinda (barra de estado)
    # ------------------------------------------------------------------
    def _crear_pie(self):
        pie = self.statusBar()
        pie.setSizeGripEnabled(False)
        self.lbl_motor = QLabel("")
        pie.addPermanentWidget(self.lbl_motor)
        pie.addPermanentWidget(QLabel("Gobierno del Estado de Michoacán de Ocampo"))

    def _mostrar_estado_conexion(self):
        if self.conexion is None:
            self.lbl_motor.setText("● Sin conexión")
        else:
            self.lbl_motor.setText(f"● {self.motor} conectado")
        self.menu_catalogos.setEnabled(self.conexion is not None)

    # ------------------------------------------------------------------
    # Conexión a la base de datos
    # ------------------------------------------------------------------
    def cambiar_motor(self, motor):
        """Crea la conexión al motor elegido con las clases de conexión que ya existen."""
        try:
            if motor == "SQL Server":
                from conexion_sqlserver import ConexionSQLServer
                nueva, marcador = ConexionSQLServer(), "?"
            else:
                from conexion_postgress import ConexionPostgresql
                nueva, marcador = ConexionPostgresql(), "%s"
            # crear_conexion() imprime mensajes con print(); se capturan para mostrarlos en una ventana
            with redirect_stdout(io.StringIO()) as salida:
                conectado = nueva.crear_conexion() is not None
            detalle = salida.getvalue().strip()
        except Exception as error:  # falta una librería, error en el .env, etc.
            conectado, detalle = False, str(error)

        if not conectado:
            aviso(self, QMessageBox.Icon.Critical, "No fue posible conectarse",
                  f"No se pudo conectar a {motor}.\n\n{detalle}")
            if self.motor in self.acciones_motor:      # se deja marcado el motor anterior
                self.acciones_motor[self.motor].setChecked(True)
            else:
                for accion in self.acciones_motor.values():
                    accion.setChecked(False)
            return False

        self._cerrar_conexion()
        self.conexion, self.marcador, self.motor = nueva, marcador, motor
        self.acciones_motor[motor].setChecked(True)
        # Los catálogos guardados pertenecían a la conexión anterior
        for widget in self.catalogos.values():
            self.pila.removeWidget(widget)
            widget.deleteLater()
        self.catalogos.clear()
        self._mostrar_estado_conexion()
        self.mostrar_inicio()
        self.statusBar().showMessage(f"Conectado a {motor}", 4000)
        return True

    def _cerrar_conexion(self):
        if self.conexion is not None:
            with redirect_stdout(io.StringIO()):
                self.conexion.cerrar_conexion()
            self.conexion = None

    # ------------------------------------------------------------------
    # Navegación
    # ------------------------------------------------------------------
    def mostrar_inicio(self):
        conteos = []
        if self.conexion is not None:
            for tabla in Menu.TABLAS.values():
                repo = RepositorioCatalogo(self.conexion, self.marcador, tabla)
                try:
                    total = repo.contar()
                except ErrorBD:
                    total = None
                conteos.append((ETIQUETAS[tabla["nombre"]], total))
        self.inicio.actualizar(conteos)
        self.pila.setCurrentWidget(self.inicio)

    def abrir_catalogo(self, clave):
        if self.conexion is None:
            aviso(self, QMessageBox.Icon.Warning, "Sin conexión",
                  "Primero elige una base de datos en el menú «Base de datos».")
            return
        if clave not in self.catalogos:
            repo = RepositorioCatalogo(self.conexion, self.marcador, Menu.TABLAS[clave])
            widget = CatalogoWidget(repo)
            widget.mensaje.connect(lambda texto: self.statusBar().showMessage(texto, 5000))
            self.catalogos[clave] = widget
            self.pila.addWidget(widget)
        widget = self.catalogos[clave]
        self.pila.setCurrentWidget(widget)
        widget.recargar()

    def acerca_de(self):
        aviso(self, QMessageBox.Icon.Information, "Acerca de",
              "Sistema de gestión de citas médicas\nCentro de Salud de Villamar\n\n"
              "Identidad gráfica: Gobierno del Estado de Michoacán\nhttps://michoacan.gob.mx/guia-grafica/")

    def closeEvent(self, evento):
        self._cerrar_conexion()
        evento.accept()


def main():
    # Se trabaja desde la carpeta del programa (o del .exe) para que se encuentre el archivo .env
    os.chdir(carpeta_app())
    app = QApplication(sys.argv)
    app.setApplicationName("Clínica Villamar")
    app.setStyle("Fusion")             # estilo base uniforme para que la hoja de estilo se vea igual en todos los equipos
    tema.cargar_fuente()               # Gibson (local o del CDN); si no está, se usa una fuente alterna
    app.setStyleSheet(tema.hoja_de_estilo())

    ventana = VentanaPrincipal()
    ventana.showMaximized()
    ventana.cambiar_motor("SQL Server")  # conexión inicial; se puede cambiar en el menú «Base de datos»
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

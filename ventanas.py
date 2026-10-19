"""Ventanas de la aplicación (PyQt6).

Aquí solo hay interfaz. Toda consulta a la base de datos se hace llamando a
RepositorioCatalogo (repositorio.py).
"""
from PyQt6.QtCore import QDate, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QIntValidator, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDateEdit,
    QDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

import iconos
import tema
from menu import Menu
from repositorio import ErrorBD

# Nombre con el que se muestra cada tabla en los menús y títulos
ETIQUETAS = {
    "Paciente": "Pacientes",
    "Medico": "Médicos",
    "Consultorio": "Consultorios",
    "Padecimiento": "Padecimientos",
    "Rol": "Roles",
    "Permiso": "Permisos",
}


def nombre_corto(etiqueta):
    """'Fecha de nacimiento (AAAA-MM-DD)' -> 'Fecha de nacimiento'."""
    return etiqueta.split(" (")[0]


def boton(texto, nombre_icono, primario=False):
    """Botón con ícono: blanco sobre guinda si es el principal, guinda sobre blanco en los demás."""
    b = QPushButton(texto)
    b.setIcon(iconos.icono(nombre_icono, tema.BLANCO if primario else tema.GUINDA, 20))
    b.setIconSize(QSize(20, 20))
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    if primario:
        b.setObjectName("primario")
    return b


def aviso(padre, icono, titulo, texto):
    """Mensaje con un solo botón 'Aceptar' (en español)."""
    caja = QMessageBox(padre)
    caja.setIcon(icono)
    caja.setWindowTitle(titulo)
    caja.setText(texto)
    caja.addButton("Aceptar", QMessageBox.ButtonRole.AcceptRole)
    caja.exec()


# ----------------------------------------------------------------------
# Formulario para Insertar y Actualizar
# ----------------------------------------------------------------------
class FormularioRegistro(QDialog):
    def __init__(self, tabla, titulo, datos=None, parent=None):
        super().__init__(parent)
        self.tabla = tabla
        self.valores = []      # se llena al presionar Guardar (mismo orden que tabla["campos"])
        self.entradas = {}     # columna -> widget de captura
        nombre = ETIQUETAS[tabla["nombre"]]
        self.setWindowTitle(f"{titulo} · {nombre}")
        self.setModal(True)
        self.setMinimumWidth(580)

        capa = QVBoxLayout(self)
        capa.setContentsMargins(28, 22, 28, 22)
        capa.setSpacing(14)

        encabezado = QLabel(f"{titulo} · {nombre}")
        encabezado.setObjectName("titulo")
        capa.addWidget(encabezado)
        capa.addWidget(QLabel("Los campos marcados con * son obligatorios."))

        formulario = QFormLayout()
        formulario.setHorizontalSpacing(18)
        formulario.setVerticalSpacing(10)
        for columna, etiqueta, obligatorio in tabla["campos"]:
            entrada = self._crear_entrada(columna)
            self.entradas[columna] = entrada
            formulario.addRow(nombre_corto(etiqueta) + (" *" if obligatorio else ""), entrada)
        capa.addLayout(formulario)

        # Aquí se muestran los errores de validación
        self.lbl_error = QLabel("")
        self.lbl_error.setObjectName("error")
        self.lbl_error.setWordWrap(True)
        self.lbl_error.hide()
        capa.addWidget(self.lbl_error)

        botones = QHBoxLayout()
        botones.addStretch()
        btn_cancelar = QPushButton("Cancelar")
        btn_guardar = QPushButton("Guardar")
        btn_guardar.setObjectName("primario")
        btn_guardar.setDefault(True)
        btn_cancelar.clicked.connect(self.reject)
        btn_guardar.clicked.connect(self.aceptar)
        botones.addWidget(btn_cancelar)
        botones.addWidget(btn_guardar)
        capa.addLayout(botones)

        if datos:
            self._rellenar(datos)

    # -- creación de los campos -------------------------------------------
    def _crear_entrada(self, columna):
        nombre = self.tabla["nombre"]
        if nombre == "Paciente" and columna == "Genero":
            combo = QComboBox()
            combo.addItems(["", "Masculino", "Femenino"])
            return combo
        if nombre == "Paciente" and columna == "FechaNacimiento":
            fecha = QDateEdit()
            fecha.setCalendarPopup(True)
            fecha.setDisplayFormat("yyyy-MM-dd")
            fecha.setMaximumDate(QDate.currentDate())   # no se permiten fechas futuras
            fecha.setDate(QDate(2000, 1, 1))
            return fecha
        return QLineEdit()

    def _leer(self, columna):
        """Valor capturado en el campo, como texto."""
        entrada = self.entradas[columna]
        if isinstance(entrada, QComboBox):
            return entrada.currentText().strip()
        if isinstance(entrada, QDateEdit):
            return entrada.date().toString("yyyy-MM-dd")
        return entrada.text().strip()

    def _rellenar(self, datos):
        """Pone en los campos los valores de un registro (diccionario con llaves en minúsculas)."""
        for columna, entrada in self.entradas.items():
            valor = datos.get(columna.lower())
            texto = "" if valor is None else str(valor)
            if isinstance(entrada, QComboBox):
                entrada.setCurrentText(texto)
            elif isinstance(entrada, QDateEdit):
                fecha = QDate.fromString(texto[:10], "yyyy-MM-dd")
                if fecha.isValid():
                    entrada.setDate(fecha)
            else:
                entrada.setText(texto)

    def como_registro(self):
        """Lo capturado hasta ahora, para reabrir el formulario si la base rechaza el dato."""
        return {c.lower(): (self._leer(c) or None) for c, _, _ in self.tabla["campos"]}

    # -- validación ---------------------------------------------------------
    def _mostrar_error(self, texto, columna):
        self.lbl_error.setText(texto)
        self.lbl_error.show()
        self.entradas[columna].setFocus()

    def aceptar(self):
        nombre = self.tabla["nombre"]
        for columna, etiqueta, obligatorio in self.tabla["campos"]:
            valor = self._leer(columna)
            if not valor and obligatorio:
                self._mostrar_error(f"El campo «{nombre_corto(etiqueta)}» es obligatorio.", columna)
                return
            error = Menu.validar(nombre, columna, valor)   # formato de teléfono, cédula, etc.
            if error:
                self._mostrar_error(error + ".", columna)
                return
        # Lo vacío se manda como None (NULL en la base)
        self.valores = [self._leer(c) or None for c, _, _ in self.tabla["campos"]]
        self.accept()


# ----------------------------------------------------------------------
# Detalle de un registro (Consultar)
# ----------------------------------------------------------------------
class DetalleRegistro(QDialog):
    def __init__(self, tabla, registro, parent=None):
        super().__init__(parent)
        nombre = ETIQUETAS[tabla["nombre"]]
        self.setWindowTitle(f"Consultar · {nombre}")
        self.setModal(True)
        self.setMinimumWidth(520)

        capa = QVBoxLayout(self)
        capa.setContentsMargins(28, 22, 28, 22)
        capa.setSpacing(14)
        titulo = QLabel(f"Consultar · {nombre}")
        titulo.setObjectName("titulo")
        capa.addWidget(titulo)

        formulario = QFormLayout()
        formulario.setHorizontalSpacing(18)
        formulario.setVerticalSpacing(8)
        filas = [("Id", tabla["pk"])] + [(nombre_corto(e), c) for c, e, _ in tabla["campos"]]
        for etiqueta, columna in filas:
            valor = registro.get(columna.lower())
            lbl = QLabel("–" if valor is None else str(valor))
            lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            lbl.setWordWrap(True)
            formulario.addRow(etiqueta, lbl)
        capa.addLayout(formulario)

        botones = QHBoxLayout()
        botones.addStretch()
        cerrar = QPushButton("Cerrar")
        cerrar.setObjectName("primario")
        cerrar.clicked.connect(self.accept)
        botones.addWidget(cerrar)
        capa.addLayout(botones)


# ----------------------------------------------------------------------
# Pantalla de un catálogo: tabla + Insertar / Actualizar / Eliminar / Consultar
# ----------------------------------------------------------------------
class CatalogoWidget(QWidget):
    mensaje = pyqtSignal(str)   # texto para la barra inferior de la ventana principal

    def __init__(self, repo, parent=None):
        super().__init__(parent)
        self.repo = repo
        self.tabla = repo.tabla
        self.registros = []     # lista de diccionarios mostrados en la tabla
        # Columnas de la tabla en pantalla: la llave primaria y luego los campos
        self.columnas = [self.tabla["pk"]] + [c for c, _, _ in self.tabla["campos"]]
        etiqueta = ETIQUETAS[self.tabla["nombre"]]

        capa = QVBoxLayout(self)
        capa.setContentsMargins(40, 28, 40, 18)
        capa.setSpacing(16)

        # Encabezado de la sección: ícono + título
        cabecera = QHBoxLayout()
        cabecera.setSpacing(16)
        icono_seccion = QLabel()
        icono_seccion.setObjectName("etiqueta_icono")
        icono_seccion.setFixedSize(56, 56)
        icono_seccion.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icono_seccion.setPixmap(iconos.pixmap(self.tabla["nombre"], tema.GUINDA, 30))
        textos = QVBoxLayout()
        textos.setSpacing(2)
        titulo = QLabel(f"Catálogo de {etiqueta.lower()}")
        titulo.setObjectName("titulo")
        subtitulo = QLabel("Selecciona un registro de la tabla para actualizarlo o eliminarlo.")
        subtitulo.setObjectName("subtitulo")
        textos.addWidget(titulo)
        textos.addWidget(subtitulo)
        cabecera.addWidget(icono_seccion)
        cabecera.addLayout(textos, 1)
        capa.addLayout(cabecera)

        # Botones del CRUD
        barra = QHBoxLayout()
        barra.setSpacing(10)
        btn_insertar = boton("Insertar", "insertar", primario=True)
        btn_actualizar = boton("Actualizar", "actualizar")
        btn_eliminar = boton("Eliminar", "eliminar")
        btn_insertar.clicked.connect(self.insertar)
        btn_actualizar.clicked.connect(self.actualizar)
        btn_eliminar.clicked.connect(self.eliminar)
        barra.addWidget(btn_insertar)
        barra.addWidget(btn_actualizar)
        barra.addWidget(btn_eliminar)
        barra.addStretch()

        # Consultar por Id
        barra.addWidget(QLabel("Id:"))
        self.txt_id = QLineEdit()
        self.txt_id.setFixedWidth(120)
        self.txt_id.setValidator(QIntValidator(1, 2147483647))
        self.txt_id.returnPressed.connect(self.consultar)
        barra.addWidget(self.txt_id)
        btn_consultar = boton("Consultar", "consultar")
        btn_todos = boton("Mostrar todos", "todos")
        btn_consultar.clicked.connect(self.consultar)
        btn_todos.clicked.connect(self.mostrar_todos)
        barra.addWidget(btn_consultar)
        barra.addWidget(btn_todos)
        capa.addLayout(barra)

        # Tabla de registros
        self.tabla_ui = QTableWidget()
        self.tabla_ui.setColumnCount(len(self.columnas))
        self.tabla_ui.setHorizontalHeaderLabels(
            ["Id"] + [nombre_corto(e) for _, e, _ in self.tabla["campos"]]
        )
        self.tabla_ui.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_ui.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla_ui.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla_ui.setAlternatingRowColors(True)
        self.tabla_ui.setShowGrid(False)
        self.tabla_ui.verticalHeader().setVisible(False)
        self.tabla_ui.verticalHeader().setDefaultSectionSize(44)
        self.tabla_ui.horizontalHeader().setStretchLastSection(True)
        self.tabla_ui.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        capa.addWidget(self.tabla_ui, 1)

        # Mensaje cuando la tabla no tiene registros
        self.lbl_vacio = QLabel("Aún no hay registros en este catálogo.\nPresiona «Insertar» para agregar el primero.")
        self.lbl_vacio.setObjectName("vacio")
        self.lbl_vacio.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_vacio.hide()
        capa.addWidget(self.lbl_vacio)
        capa.addStretch()

    # -- utilidades -----------------------------------------------------
    def _seleccionado(self):
        """Registro (diccionario) de la fila seleccionada o None si no hay ninguna."""
        fila = self.tabla_ui.currentRow()
        if fila < 0 or fila >= len(self.registros):
            aviso(self, QMessageBox.Icon.Information, "Selecciona un registro",
                  "Primero selecciona un registro de la tabla.")
            return None
        return self.registros[fila]

    def _id_de(self, registro):
        return registro[self.tabla["pk"].lower()]

    def _llenar_tabla(self):
        self.tabla_ui.setRowCount(len(self.registros))
        for fila, registro in enumerate(self.registros):
            for col, columna in enumerate(self.columnas):
                valor = registro.get(columna.lower())
                item = QTableWidgetItem("" if valor is None else str(valor))
                if col == 0:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla_ui.setItem(fila, col, item)
        self.tabla_ui.resizeColumnsToContents()

    # -- CONSULTAR (todos) --------------------------------------------------
    def recargar(self):
        try:
            self.registros = self.repo.consultar_todos()
        except ErrorBD as error:
            aviso(self, QMessageBox.Icon.Critical, "No se pudieron consultar los datos", str(error))
            return
        self._llenar_tabla()
        hay_datos = len(self.registros) > 0
        self.tabla_ui.setVisible(hay_datos)
        self.lbl_vacio.setVisible(not hay_datos)
        self.mensaje.emit(f"{len(self.registros)} registros en {ETIQUETAS[self.tabla['nombre']].lower()}")

    def mostrar_todos(self):
        self.txt_id.clear()
        self.recargar()

    # -- CONSULTAR (por Id) ----------------------------------------------------
    def consultar(self):
        texto = self.txt_id.text().strip()
        if not texto.isdigit():
            aviso(self, QMessageBox.Icon.Warning, "Consultar", "Escribe el Id del registro (un número entero).")
            return
        try:
            registro = self.repo.consultar_por_id(int(texto))
        except ErrorBD as error:
            aviso(self, QMessageBox.Icon.Critical, "No se pudo consultar", str(error))
            return
        if registro is None:
            aviso(self, QMessageBox.Icon.Information, "Consultar", f"No existe un registro con el Id {texto}.")
            return
        DetalleRegistro(self.tabla, registro, self).exec()

    # -- INSERTAR ---------------------------------------------------------------
    def insertar(self):
        datos = None
        while True:
            formulario = FormularioRegistro(self.tabla, "Insertar", datos, self)
            if formulario.exec() != QDialog.DialogCode.Accepted:
                return
            try:
                self.repo.insertar(formulario.valores)
                break
            except ErrorBD as error:
                aviso(self, QMessageBox.Icon.Warning, "No se pudo insertar el registro", str(error))
                datos = formulario.como_registro()   # se reabre con lo que ya había capturado
        self.recargar()
        self.mensaje.emit("Registro insertado correctamente")

    # -- ACTUALIZAR ---------------------------------------------------------------
    def actualizar(self):
        seleccionado = self._seleccionado()
        if seleccionado is None:
            return
        id_registro = self._id_de(seleccionado)
        try:
            datos = self.repo.consultar_por_id(id_registro)   # se lee de nuevo de la base
        except ErrorBD as error:
            aviso(self, QMessageBox.Icon.Critical, "No se pudo consultar", str(error))
            return
        if datos is None:
            aviso(self, QMessageBox.Icon.Information, "Actualizar", "El registro ya no existe.")
            self.recargar()
            return
        while True:
            formulario = FormularioRegistro(self.tabla, "Actualizar", datos, self)
            if formulario.exec() != QDialog.DialogCode.Accepted:
                return
            try:
                self.repo.actualizar(id_registro, formulario.valores)
                break
            except ErrorBD as error:
                aviso(self, QMessageBox.Icon.Warning, "No se pudo actualizar el registro", str(error))
                datos = formulario.como_registro()
        self.recargar()
        self.mensaje.emit("Registro actualizado correctamente")

    # -- ELIMINAR --------------------------------------------------------------------
    def eliminar(self):
        seleccionado = self._seleccionado()
        if seleccionado is None:
            return
        id_registro = self._id_de(seleccionado)

        caja = QMessageBox(self)
        caja.setIcon(QMessageBox.Icon.Question)
        caja.setWindowTitle("Eliminar registro")
        caja.setText(f"¿Deseas eliminar el registro con Id {id_registro}?\nEsta acción no se puede deshacer.")
        btn_si = caja.addButton("Sí, eliminar", QMessageBox.ButtonRole.AcceptRole)
        btn_no = caja.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
        caja.setDefaultButton(btn_no)
        caja.exec()
        if caja.clickedButton() is not btn_si:
            return

        try:
            self.repo.eliminar(id_registro)
        except ErrorBD as error:
            aviso(self, QMessageBox.Icon.Warning, "No se pudo eliminar",
                  "No se pudo eliminar el registro. Es posible que otra tabla lo esté usando "
                  f"(por ejemplo, citas relacionadas).\n\nDetalle: {error}")
            return
        self.recargar()
        self.mensaje.emit("Registro eliminado correctamente")


# ----------------------------------------------------------------------
# Pantalla de inicio: imagen institucional + tarjetas de los catálogos
# ----------------------------------------------------------------------
class PanelImagen(QWidget):
    """Panel con imagen de fondo que cubre todo el espacio (como un 'cover')."""

    def __init__(self, ruta, oscurecer, parent=None):
        super().__init__(parent)
        self._pix = QPixmap(str(ruta)) if ruta else QPixmap()
        self._oscurecer = oscurecer      # True: velo guinda encima (para fotografías)
        self._cache = None               # (tamaño, imagen ya escalada)
        self.setMinimumWidth(380)
        self.capa = QVBoxLayout(self)
        self.capa.setContentsMargins(44, 44, 44, 48)

    def paintEvent(self, evento):
        pintor = QPainter(self)
        pintor.fillRect(self.rect(), QColor(tema.GUINDA))
        if not self._pix.isNull():
            if self._cache is None or self._cache[0] != self.size():
                escalada = self._pix.scaled(
                    self.size(),
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self._cache = (self.size(), escalada)
            escalada = self._cache[1]
            x = (escalada.width() - self.width()) // 2
            y = (escalada.height() - self.height()) // 2
            pintor.drawPixmap(0, 0, escalada, x, y, self.width(), self.height())
        if self._oscurecer:
            pintor.fillRect(self.rect(), QColor(74, 0, 31, 205))
        pintor.end()


class TarjetaCatalogo(QFrame):
    """Tarjeta clicable de un catálogo: ícono, nombre y cantidad de registros."""

    abrir = pyqtSignal()

    def __init__(self, nombre_tabla, etiqueta, parent=None):
        super().__init__(parent)
        self.setObjectName("tarjeta")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(120)

        capa = QHBoxLayout(self)
        capa.setContentsMargins(24, 18, 24, 18)
        capa.setSpacing(18)
        icono_tarjeta = QLabel()
        icono_tarjeta.setObjectName("etiqueta_icono")
        icono_tarjeta.setFixedSize(56, 56)
        icono_tarjeta.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icono_tarjeta.setPixmap(iconos.pixmap(nombre_tabla, tema.GUINDA, 30))

        textos = QVBoxLayout()
        textos.setSpacing(4)
        textos.addStretch()
        lbl_nombre = QLabel(etiqueta)
        lbl_nombre.setObjectName("tarjeta_titulo")
        self.lbl_conteo = QLabel("–")
        self.lbl_conteo.setObjectName("tarjeta_conteo")
        textos.addWidget(lbl_nombre)
        textos.addWidget(self.lbl_conteo)
        textos.addStretch()

        capa.addWidget(icono_tarjeta)
        capa.addLayout(textos, 1)

    def poner_total(self, total):
        if total is None:
            self.lbl_conteo.setText("Sin conexión")
        else:
            self.lbl_conteo.setText("1 registro" if total == 1 else f"{total} registros")

    def mousePressEvent(self, evento):
        if evento.button() == Qt.MouseButton.LeftButton:
            self.abrir.emit()
        super().mousePressEvent(evento)


class InicioWidget(QWidget):
    abrir = pyqtSignal(str)   # clave del catálogo (Menu.TABLAS) que se quiere abrir

    def __init__(self, parent=None):
        super().__init__(parent)
        fila = QHBoxLayout(self)
        fila.setContentsMargins(0, 0, 0, 0)
        fila.setSpacing(0)

        # Imagen de la izquierda: si pones tu propia foto en imagenes/fondo.jpg se usa con un
        # velo guinda; si no, se usa el fondo institucional que viene incluido.
        foto = None
        for nombre in ("fondo.jpg", "fondo.jpeg", "fondo.png"):
            foto = iconos.buscar("imagenes/" + nombre)
            if foto:
                break
        if foto:
            panel = PanelImagen(foto, True)
        else:
            panel = PanelImagen(iconos.buscar("imagenes/fondo_inicio.png"), False)

        panel.capa.addStretch()
        for texto, estilo in (
            ("Centro de Salud\nde Villamar", "font-size: 38px; font-weight: bold; color: white;"),
            ("Sistema de gestión de citas médicas", "font-size: 20px; color: white;"),
            ("Secretaría de Salud · Gobierno de Michoacán", f"font-size: 16px; color: {tema.ROSA_CLARO};"),
        ):
            lbl = QLabel(texto)
            lbl.setWordWrap(True)
            lbl.setStyleSheet(estilo + " background: transparent;")
            panel.capa.addWidget(lbl)
        panel.capa.addSpacing(8)
        fila.addWidget(panel, 4)

        # Lado derecho: bienvenida y tarjetas
        derecha = QWidget()
        capa = QVBoxLayout(derecha)
        capa.setContentsMargins(56, 44, 56, 28)
        capa.setSpacing(12)

        titulo = QLabel("Bienvenido(a)")
        titulo.setObjectName("titulo")
        subtitulo = QLabel("Administra los catálogos del sistema eligiendo una tarjeta o desde el menú Catálogos.")
        subtitulo.setObjectName("subtitulo")
        subtitulo.setWordWrap(True)
        seccion = QLabel("Catálogos")
        seccion.setObjectName("seccion")
        capa.addWidget(titulo)
        capa.addWidget(subtitulo)
        capa.addSpacing(16)
        capa.addWidget(seccion)

        cuadricula = QGridLayout()
        cuadricula.setHorizontalSpacing(18)
        cuadricula.setVerticalSpacing(18)
        self.tarjetas = {}   # etiqueta -> TarjetaCatalogo
        for i, (clave, tabla) in enumerate(Menu.TABLAS.items()):
            etiqueta = ETIQUETAS[tabla["nombre"]]
            tarjeta = TarjetaCatalogo(tabla["nombre"], etiqueta)
            tarjeta.abrir.connect(lambda c=clave: self.abrir.emit(c))
            cuadricula.addWidget(tarjeta, i // 2, i % 2)
            self.tarjetas[etiqueta] = tarjeta
        cuadricula.setColumnStretch(0, 1)
        cuadricula.setColumnStretch(1, 1)
        capa.addLayout(cuadricula)
        capa.addStretch()
        fila.addWidget(derecha, 7)

    def actualizar(self, conteos):
        """conteos: lista de (etiqueta, total); vacía si no hay conexión."""
        datos = dict(conteos)
        for etiqueta, tarjeta in self.tarjetas.items():
            tarjeta.poner_total(datos.get(etiqueta))

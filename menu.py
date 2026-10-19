import json
import re
from datetime import date, datetime


class Menu:
    """Menú principal con el CRUD de las tablas maestras de ClinicaVillamar.

    El usuario elige la tabla (Paciente, Medico, Consultorio, Padecimiento,
    Rol o Permiso) y después realiza Crear, Consultar, Actualizar o Eliminar.

    Funciona con cualquiera de las dos clases de conexión
    (ConexionSQLServer o ConexionPostgresql), ya que ambas exponen
    ejecutar_consulta(sql, parametros) y regresan un JSON.

    - SQL Server (mssql_python) usa el marcador de parámetros "?"
    - PostgreSQL (psycopg2)     usa el marcador de parámetros "%s"
    """

    # Definición de cada tabla maestra:
    #   pk     -> nombre de la llave primaria (autoincremental, no se captura)
    #   campos -> (columna, etiqueta, obligatorio)
    TABLAS = {
        "1": {
            "nombre": "Paciente",
            "pk": "Id_Paciente",
            "campos": [
                ("Nombre", "Nombre", True),
                ("ApellidoPaterno", "Apellido paterno", True),
                ("ApellidoMaterno", "Apellido materno", False),
                ("FechaNacimiento", "Fecha de nacimiento (AAAA-MM-DD)", True),
                ("Genero", "Género (Masculino/Femenino)", True),
                ("Telefono", "Teléfono", False),
                ("Calle", "Calle", True),
                ("Numero", "Número", True),
                ("Colonia", "Colonia", True),
                ("CodigoPostal", "Código postal", True),
                ("Ciudad", "Ciudad", True),
            ],
        },
        "2": {
            "nombre": "Medico",
            "pk": "Id_Medico",
            "campos": [
                ("Nombre", "Nombre", True),
                ("ApellidoPaterno", "Apellido(s)", True),
                ("Especialidad", "Especialidad", True),
                ("CedulaProfesional", "Cédula profesional", True),
            ],
        },
        "3": {
            "nombre": "Consultorio",
            "pk": "Id_Consultorio",
            "campos": [
                ("Numero", "Número", True),
                ("Descripcion", "Descripción", False),
            ],
        },
        "4": {
            "nombre": "Padecimiento",
            "pk": "Id_Padecimiento",
            "campos": [
                ("Nombre", "Nombre", True),
                ("ClaveCIE10", "Clave CIE-10", True),
                ("Descripcion", "Descripción", False),
            ],
        },
        "5": {
            "nombre": "Rol",
            "pk": "Id_Rol",
            "campos": [
                ("Nombre", "Nombre", True),
                ("Descripcion", "Descripción", False),
            ],
        },
        "6": {
            "nombre": "Permiso",
            "pk": "Id_Permiso",
            "campos": [
                ("Nombre", "Nombre", True),
                ("Descripcion", "Descripción", False),
            ],
        },
    }

    # Reglas de validación: reflejan los CHECK de la base de datos para avisar
    # al usuario antes de enviar el dato (clave: (tabla, columna)).
    REGLAS = {
        ("Paciente", "Genero"): (r"^(Masculino|Femenino)$", "El género debe ser Masculino o Femenino"),
        ("Paciente", "Telefono"): (r"^[0-9]{10}$", "El teléfono debe tener 10 dígitos"),
        ("Paciente", "CodigoPostal"): (r"^[0-9]{5}$", "El código postal debe tener 5 dígitos"),
        ("Medico", "CedulaProfesional"): (r"^[0-9]{7,8}$", "La cédula profesional debe tener 7 u 8 dígitos"),
    }

    # Mensajes amigables para los errores que regresa la base de datos
    # (se busca el nombre de la restricción dentro del texto del error).
    ERRORES_BD = [
        ("uq_medico_cedula", "Ya existe un médico con esa cédula profesional"),
        ("chk_medico_cedula", "La cédula profesional debe tener 7 u 8 dígitos"),
        ("uq_consultorio_numero", "Ya existe un consultorio con ese número"),
        ("uq_padecimiento_clave", "Ya existe un padecimiento con esa clave CIE-10"),
        ("uq_rol_nombre", "Ya existe un rol con ese nombre"),
        ("uq_permiso_nombre", "Ya existe un permiso con ese nombre"),
        ("chk_paciente_genero", "El género debe ser Masculino o Femenino"),
        ("chk_paciente_fechanac", "La fecha de nacimiento no puede ser futura"),
        ("chk_paciente_telefono", "El teléfono debe tener 10 dígitos"),
        ("chk_paciente_cp", "El código postal debe tener 5 dígitos"),
        ("chk_paciente_codigopostal", "El código postal debe tener 5 dígitos"),
    ]

    def __init__(self, conexion, marcador):
        self.conexion = conexion
        self.p = marcador  # "?" o "%s"
        self.tabla = None  # Tabla seleccionada actualmente

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------
    def _ejecutar(self, sql, parametros=None):
        resultado = json.loads(self.conexion.ejecutar_consulta(sql, parametros))
        if not resultado.get("estado"):
            detalle = resultado.get("error") or resultado.get("mensaje")
            if detalle:
                detalle = self.traducir_error(detalle)
            print(f"\n[ERROR] {resultado.get('mensaje')}")
            if detalle and detalle != resultado.get("mensaje"):
                print(f"        {detalle}")
            return None
        return resultado

    @staticmethod
    def validar(tabla, columna, valor):
        """Regresa un mensaje de error si el valor no cumple las reglas, o None si es válido."""
        if not valor:  # lo vacío lo controla el campo "obligatorio"
            return None
        if (tabla, columna) == ("Paciente", "FechaNacimiento"):
            try:
                fecha = datetime.strptime(valor, "%Y-%m-%d").date()
            except ValueError:
                return "La fecha debe tener el formato AAAA-MM-DD"
            if fecha > date.today():
                return "La fecha de nacimiento no puede ser futura"
            return None
        regla = Menu.REGLAS.get((tabla, columna))
        if regla and not re.match(regla[0], valor):
            return regla[1]
        return None

    @staticmethod
    def traducir_error(texto):
        """Cambia el texto técnico de la base de datos por un mensaje claro, si lo conoce."""
        bajo = str(texto).lower()
        for fragmento, mensaje in Menu.ERRORES_BD:
            if fragmento in bajo:
                return mensaje
        return texto

    @staticmethod
    def _normalizar(registro):
        # Postgres regresa las columnas en minúsculas y SQL Server tal cual,
        # por eso se pasan todas a minúsculas.
        return {k.lower(): v for k, v in registro.items()}

    def _pedir_id(self):
        texto = input(f"{self.tabla['pk']}: ").strip()
        if not texto.isdigit():
            print("\n[ERROR] El Id debe ser un número entero.")
            return None
        return int(texto)

    def _obtener(self, id_registro):
        t = self.tabla
        res = self._ejecutar(
            f"SELECT * FROM {t['nombre']} WHERE {t['pk']} = {self.p}", (id_registro,)
        )
        if res and res["registros"]:
            return self._normalizar(res["registros"][0])
        return None

    def _mostrar(self, registro):
        t = self.tabla
        partes = []
        for columna, etiqueta, _ in t["campos"]:
            valor = registro[columna.lower()]
            partes.append(f"{etiqueta}: {valor if valor is not None else '-'}")
        print(f"  [{registro[t['pk'].lower()]}] " + " | ".join(partes))

    # ------------------------------------------------------------------
    # CRUD (sobre la tabla seleccionada)
    # ------------------------------------------------------------------
    def crear(self):
        t = self.tabla
        print(f"\n--- CREAR EN {t['nombre'].upper()} ---")
        valores = []
        for columna, etiqueta, obligatorio in t["campos"]:
            while True:
                dato = input(f"{etiqueta}: ").strip()
                if not dato and obligatorio:
                    print("  Este campo es obligatorio.")
                    continue
                error = self.validar(t["nombre"], columna, dato)
                if error:
                    print(f"  {error}.")
                    continue
                valores.append(dato or None)
                break

        columnas = ", ".join(c for c, _, _ in t["campos"])
        marcadores = ", ".join([self.p] * len(t["campos"]))
        res = self._ejecutar(
            f"INSERT INTO {t['nombre']} ({columnas}) VALUES ({marcadores})",
            tuple(valores),
        )
        if res:
            print("\nRegistro creado correctamente.")

    def consultar(self):
        t = self.tabla
        print(f"\n--- CONSULTAR {t['nombre'].upper()} ---")
        print("1. Ver todos")
        print("2. Buscar por Id")
        opcion = input("Opción: ").strip()

        if opcion == "1":
            res = self._ejecutar(f"SELECT * FROM {t['nombre']} ORDER BY {t['pk']}")
            if res is None:
                return
            if not res["registros"]:
                print("\nNo hay registros.")
                return
            print()
            for r in res["registros"]:
                self._mostrar(self._normalizar(r))
                print()
            print(f"\nTotal: {len(res['registros'])} registro(s).")
        elif opcion == "2":
            id_registro = self._pedir_id()
            if id_registro is None:
                return
            registro = self._obtener(id_registro)
            if registro:
                print()
                self._mostrar(registro)
            else:
                print("\nNo se encontró un registro con ese Id.")
        else:
            print("\nOpción no válida.")

    def actualizar(self):
        t = self.tabla
        print(f"\n--- ACTUALIZAR EN {t['nombre'].upper()} ---")
        id_registro = self._pedir_id()
        if id_registro is None:
            return
        actual = self._obtener(id_registro)
        if not actual:
            print("\nNo se encontró un registro con ese Id.")
            return

        print("\nDatos actuales:")
        self._mostrar(actual)
        print("\nEscribe el nuevo valor o presiona Enter para dejarlo igual.")

        asignaciones, valores = [], []
        for columna, etiqueta, _ in t["campos"]:
            anterior = actual[columna.lower()]
            dato = input(
                f"{etiqueta} [{anterior if anterior is not None else ''}]: "
            ).strip()
            if dato:
                error = self.validar(t["nombre"], columna, dato)
                if error:
                    print(f"  {error}. Se conserva el valor anterior.")
                    continue
                asignaciones.append(f"{columna} = {self.p}")
                valores.append(dato)

        if not asignaciones:
            print("\nNo se modificó ningún dato.")
            return

        valores.append(id_registro)
        res = self._ejecutar(
            f"UPDATE {t['nombre']} SET {', '.join(asignaciones)} "
            f"WHERE {t['pk']} = {self.p}",
            tuple(valores),
        )
        if res:
            print("\nRegistro actualizado correctamente.")

    def eliminar(self):
        t = self.tabla
        print(f"\n--- ELIMINAR DE {t['nombre'].upper()} ---")
        id_registro = self._pedir_id()
        if id_registro is None:
            return
        actual = self._obtener(id_registro)
        if not actual:
            print("\nNo se encontró un registro con ese Id.")
            return

        print()
        self._mostrar(actual)
        confirmar = input("\n¿Seguro que deseas eliminarlo? (s/n): ").strip().lower()
        if confirmar != "s":
            print("\nOperación cancelada.")
            return

        res = self._ejecutar(
            f"DELETE FROM {t['nombre']} WHERE {t['pk']} = {self.p}", (id_registro,)
        )
        if res:
            print("\nRegistro eliminado correctamente.")
        else:
            print("(Si otras tablas hacen referencia a este registro, no se puede eliminar.)")

    # ------------------------------------------------------------------
    # Menús
    # ------------------------------------------------------------------
    def menu_crud(self):
        while True:
            print(f"\n========== TABLA: {self.tabla['nombre'].upper()} ==========")
            print("1. Crear")
            print("2. Consultar")
            print("3. Actualizar")
            print("4. Eliminar")
            print("5. Volver a la selección de tabla")
            opcion = input("Selecciona una opción: ").strip()

            if opcion == "1":
                self.crear()
            elif opcion == "2":
                self.consultar()
            elif opcion == "3":
                self.actualizar()
            elif opcion == "4":
                self.eliminar()
            elif opcion == "5":
                break
            else:
                print("\nOpción no válida, intenta de nuevo.")

    def mostrar_menu(self):
        while True:
            print("\n========== CLÍNICA VILLAMAR - TABLAS MAESTRAS ==========")
            for clave, t in self.TABLAS.items():
                print(f"{clave}. {t['nombre']}")
            print("0. Salir")
            opcion = input("Selecciona la tabla con la que deseas trabajar: ").strip()

            if opcion == "0":
                print("\nSaliendo del programa...")
                break
            elif opcion in self.TABLAS:
                self.tabla = self.TABLAS[opcion]
                self.menu_crud()
            else:
                print("\nOpción no válida, intenta de nuevo.")
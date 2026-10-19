"""Acceso a datos del CRUD de catálogos (tablas maestras).

Esta clase es la ÚNICA que habla con la base de datos. La interfaz gráfica
(ventanas.py) nunca escribe SQL: solo llama a los métodos de aquí.

Usa la clase de conexión que ya existe (ConexionSQLServer o ConexionPostgresql).
Ambas exponen el mismo método:

    ejecutar_consulta(sql, parametros) -> texto JSON

y el JSON trae siempre la llave "estado" (True/False). En un SELECT también
trae "registros" (lista de diccionarios).

Marcador de parámetros (el "hueco" donde va el valor):
    - SQL Server (mssql_python)  -> "?"
    - PostgreSQL (psycopg2)      -> "%s"
Los valores NUNCA se pegan dentro del texto SQL; se mandan aparte en
`parametros`. Así el motor los trata como datos y no como código
(evita la inyección SQL y los problemas con comillas).
"""
import json

from menu import Menu  # se reutilizan TABLAS, traducir_error y _normalizar


class ErrorBD(Exception):
    """Error al ejecutar una consulta. Su texto ya está listo para mostrarse al usuario."""


class RepositorioCatalogo:
    def __init__(self, conexion, marcador, tabla):
        self.conexion = conexion          # objeto ConexionSQLServer o ConexionPostgresql
        self.p = marcador                 # "?" o "%s"
        self.tabla = tabla                # diccionario de Menu.TABLAS
        self.nombre = tabla["nombre"]     # p. ej. "Medico"
        self.pk = tabla["pk"]             # p. ej. "Id_Medico"
        # Columnas que captura el usuario (la llave primaria es autoincremental)
        self.columnas = [columna for columna, _, _ in tabla["campos"]]

    # ------------------------------------------------------------------
    # Método central: todas las consultas pasan por aquí
    # ------------------------------------------------------------------
    def _ejecutar(self, sql, parametros=None):
        # 1) Se envía el SQL y los parámetros a la clase de conexión.
        #    Ella ejecuta, hace commit si corresponde y regresa un TEXTO JSON.
        texto_json = self.conexion.ejecutar_consulta(sql, parametros)
        # 2) json.loads convierte ese texto en un diccionario de Python.
        resultado = json.loads(texto_json)
        # 3) Si "estado" no es True hubo un error (restricción, conexión, etc.).
        if not resultado.get("estado"):
            detalle = " ".join(
                str(x) for x in (resultado.get("mensaje"), resultado.get("error")) if x
            ) or "Error desconocido"
            # Se cambia el texto técnico del motor por uno claro (ver Menu.ERRORES_BD)
            raise ErrorBD(Menu.traducir_error(" ".join(detalle.split())))
        return resultado

    # ------------------------------------------------------------------
    # CONSULTAR
    # ------------------------------------------------------------------
    def consultar_todos(self):
        """SELECT de toda la tabla, ordenada por su llave primaria."""
        sql = f"SELECT * FROM {self.nombre} ORDER BY {self.pk}"
        resultado = self._ejecutar(sql)
        # Postgres regresa los nombres de columna en minúsculas y SQL Server no;
        # _normalizar los pasa todos a minúsculas para tratarlos igual.
        return [Menu._normalizar(fila) for fila in resultado["registros"]]

    def consultar_por_id(self, id_registro):
        """SELECT de un solo registro. Regresa un diccionario o None si no existe."""
        sql = f"SELECT * FROM {self.nombre} WHERE {self.pk} = {self.p}"
        # (id_registro,) es una tupla de un elemento: la coma es obligatoria
        resultado = self._ejecutar(sql, (id_registro,))
        if resultado["registros"]:
            return Menu._normalizar(resultado["registros"][0])
        return None

    def contar(self):
        """Cantidad de registros de la tabla (se usa en la pantalla de inicio)."""
        resultado = self._ejecutar(f"SELECT COUNT(*) AS total FROM {self.nombre}")
        return Menu._normalizar(resultado["registros"][0])["total"]

    # ------------------------------------------------------------------
    # INSERTAR
    # ------------------------------------------------------------------
    def insertar(self, valores):
        """INSERT de un registro nuevo. `valores` va en el mismo orden que self.columnas."""
        columnas = ", ".join(self.columnas)                    # "Nombre, ApellidoPaterno, ..."
        huecos = ", ".join([self.p] * len(self.columnas))      # "?, ?, ?, ?"
        sql = f"INSERT INTO {self.nombre} ({columnas}) VALUES ({huecos})"
        # La llave primaria no se manda: la base la genera sola (identity / serial)
        self._ejecutar(sql, tuple(valores))

    # ------------------------------------------------------------------
    # ACTUALIZAR
    # ------------------------------------------------------------------
    def actualizar(self, id_registro, valores):
        """UPDATE de todos los campos del registro con ese Id."""
        asignaciones = ", ".join(f"{columna} = {self.p}" for columna in self.columnas)
        sql = f"UPDATE {self.nombre} SET {asignaciones} WHERE {self.pk} = {self.p}"
        # Los huecos se llenan en orden: primero los valores del SET y al final el Id del WHERE
        self._ejecutar(sql, tuple(valores) + (id_registro,))

    # ------------------------------------------------------------------
    # ELIMINAR
    # ------------------------------------------------------------------
    def eliminar(self, id_registro):
        """DELETE del registro con ese Id.

        Falla (ErrorBD) si otra tabla lo referencia con una llave foránea;
        por ejemplo, un médico que ya tiene citas.
        """
        sql = f"DELETE FROM {self.nombre} WHERE {self.pk} = {self.p}"
        self._ejecutar(sql, (id_registro,))

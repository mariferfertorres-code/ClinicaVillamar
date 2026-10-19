import mssql_python
import json
import os
from dotenv import load_dotenv


class ConexionSQLServer():
    def __init__(self):
        load_dotenv() # Podemos compartir el código sin compartir datos sensibles
        self.SERVER = os.environ.get("SERVER_NAME")
        self.DATABASE_NAME = os.environ.get("DATABASE_NAME")
        self.USER = os.environ.get("USER")
        self.PASSWORD = os.environ.get("PASSWORD")

        self.CNX = None # Gestionar la conexión
        self.CURSOR = None # Gestionar la consulta

    def crear_conexion(self):
        # Crear la cadena de conexión
        try:
            cadena_conexion = (
                f"Server={self.SERVER};"
                f"Database={self.DATABASE_NAME};"
                f"UID={self.USER};"
                f"PWD={self.PASSWORD};"
                "Encrypt=yes;"
                "TrustServerCertificate=yes;"
            )

            self.CNX = mssql_python.connect(cadena_conexion)
            self.CURSOR = self.CNX.cursor()
            print(f"Conectado al servidor {self.SERVER}")
            return self.CNX
        except mssql_python.Error as e:
            print(f"Error al conectarse al servidor {self.SERVER} de Base de Datos...")
            print(e)
            self.CNX = None
            self.CURSOR = None
            return None

    # Método para realizar consultas  SQL a la Base de Datos
    def ejecutar_consulta(self, sql, parametros=None):
        try:
            # Verificar conexión
            if self.CNX is None:
                # Intento conectarme
                if self.crear_conexion() is None:
                    return json.dumps(
                        {
                            "estado": False,
                            "mensaje": "No fue posible establecer la conexión"
                        },
                        ensure_ascii=False # Si hay un carácter raro que no lo tome en cuenta
                    )

            # Ejecutar consulta
            if parametros:
                self.CURSOR.execute(
                    sql,
                    parametros
                )
            else:
                self.CURSOR.execute(sql)

            # Identificar operación (SELECT, UPDATE)
            tipo = sql.strip().split()[0].upper()
            # SELECT
            if tipo == "SELECT":
                columnas=[]
                for columna in self.CURSOR.description:
                    columnas.append(columna[0])

                # Obtener registros
                registros = self.CURSOR.fetchall() #Regresa todos los registros y los guarda en la var registros

                resultado = []
                for registro in registros:
                    fila = {}
                    for i, valor in enumerate(registro):
                        fila[columnas[i]] = valor
                    resultado.append(fila)

                return json.dumps(
                    {
                        "estado": True,
                        "tipo": "SELECT",
                        "registros": resultado
                    },
                    default=str, # Si no sabe como convertir, aplicale la funcion str()
                    ensure_ascii=False # Para caracteres latinoamericanos
                )
            # INSERT
            elif tipo == "INSERT":
                filas = self.CURSOR.rowcount # Obtine el numero de rgistros afectados
                self.CNX.commit() # Comete la transacción
                return json.dumps(
                    {
                        "estado": True,
                        "tipo": "INSERT",
                        "mensaje": "Registro insertado correctamente",
                        "filas_afectadas": filas
                    },
                    ensure_ascii=False
                )
            # UPDATE
            elif tipo == "UPDATE":
                filas = self.CURSOR.rowcount
                self.CNX.commit()
                return json.dumps(
                    {
                        "estado": True,
                        "tipo": "UPDATE",
                        "mensaje": "Registro actualizado correctamente",
                        "filas_afectadas": filas
                    },
                    ensure_ascii=False
                )
            # DELETE
            elif tipo == "DELETE":
                filas = self.CURSOR.rowcount
                self.CNX.commit()
                return json.dumps(
                    {
                        "estado": True,
                        "tipo": "DELETE",
                        "mensaje": "Registro eliminado correctamente",
                        "filas_afectadas": filas
                    },
                    ensure_ascii=False
                )
            # OTRAS OPERACIONES
            else:
                filas = self.CURSOR.rowcount
                self.CNX.commit()
                return json.dumps(
                    {
                        "estado": True,
                        "tipo": tipo,
                        "mensaje": "Consulta ejecutada correctamente",
                        "filas_afectadas": filas
                    },
                    ensure_ascii=False
                )
        # ERROR DE INTEGRIDAD
        except mssql_python.IntegrityError as e:
            if self.CNX:
                self.CNX.rollback()
            return json.dumps(
                {
                    "estado": False,
                    "tipo": "IntegrityError",
                    "mensaje": "Violación de integridad en la base de datos",
                    "error": str(e)
                },
                ensure_ascii=False
            )
        # ERROR DE PROGRAMACIÓN SQL
        except mssql_python.ProgrammingError as e:
            if self.CNX:
                self.CNX.rollback()
            return json.dumps(
                {
                    "estado": False,
                    "tipo": "ProgrammingError",
                    "mensaje": "Error en la consulta SQL",
                    "error": str(e)
                },
                ensure_ascii=False
            )
        # ERROR GENERAL
        except mssql_python.Error as e:
            if self.CNX:
                self.CNX.rollback()
            return json.dumps(
                {
                    "estado": False,
                    "tipo": "DatabaseError",
                    "mensaje": "Error en la base de datos",
                    "error": str(e)
                },
                ensure_ascii=False
            )
        # ERROR DE PYTHON
        except Exception as e:
            if self.CNX:
                self.CNX.rollback()
            return json.dumps(
                {
                    "estado": False,
                    "tipo": "Error",
                    "mensaje": "Error inesperado",
                    "error": str(e)
                },
                ensure_ascii=False
            )

    # Método para cerrar la conexión de la Base de Datos
    def cerrar_conexion(self):
        try:
            if self.CURSOR:
                self.CURSOR.close()
                self.CURSOR = None

            if self.CNX:
                self.CNX.close()
                self.CNX = None

            print(F"Se ha cerrado la conexión al servidor {self.SERVER}")
            return True
        except mssql_python.Error as e:
            print(f"Error al desconectarse del servidor de la Base de Datos")
            print(e)
            return False

if __name__ == '__main__':
    cnn = ConexionSQLServer()
    cnn.crear_conexion()
    sql = """
            SELECT * from Paciente
            """
    parametros = {}
    result = json.loads(cnn.ejecutar_consulta(sql, parametros))
    cnn.cerrar_conexion()
    for r in result["registros"]:
        print(r)
        print()
    
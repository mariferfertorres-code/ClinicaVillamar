import psycopg2
import json
import os
from dotenv import load_dotenv
from datetime import date, datetime


# Función auxiliar para convertir datos tipo fecha o decimal a JSON sin errores
def serializador_personalizado(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Tipo {type(obj)} no es serializable en JSON")


class ConexionPostgresql:
    def __init__(self):
        # En PostgreSQL los nombres de servidor locales suelen ser 'localhost' o '127.0.0.1'
        load_dotenv()
        self.HOST = os.environ.get("PG_HOST", "localhost")
        self.PORT = os.environ.get("PG_PORT", "5432")  # Puerto por defecto de PostgreSQL
        self.DATABASE_NAME = os.environ.get("PG_DATABASE")  # En Postgres se acostumbra minúsculas
        self.USER = os.environ.get("PG_USER")  # Usuario por defecto de Postgres
        self.PASSWORD = os.environ.get("PG_PASSWORD")

        self.CNX = None  # Gestionar la conexión
        self.CURSOR = None  # Gestionar las consultas

    # ---------------------------------------------------------------------------------------------------------------------------------

    def crear_conexion(self):
        try:
            # En psycopg2 se pueden pasar los parámetros directamente
            self.CNX = psycopg2.connect(
                host=self.HOST,
                port=self.PORT,
                dbname=self.DATABASE_NAME,
                user=self.USER,
                password=self.PASSWORD,
            )
            self.CURSOR = self.CNX.cursor()
            print(
                f"Conexión exitosa a la base de datos PostgreSQL en {self.HOST}."
            )
            return self.CNX
        except psycopg2.Error as e:
            print(
                f"Error al conectar a la base de datos PostgreSQL: {self.HOST}"
            )
            print(e)
            self.CNX = None
            self.CURSOR = None
            return None

    # ---------------------------------------------------------------------------------------------------------------------------------

    # Método para realizar consultas a la base de datos
    def ejecutar_consulta(self, sql, parametros=None):
        try:
            # Verificar la conexión
            if self.CNX is None or self.CNX.closed:
                if self.crear_conexion() is None:
                    return json.dumps(
                        {
                            "estado": False,
                            "mensaje": "No se pudo establecer la conexión a la base de datos PostgreSQL.",
                        },
                        ensure_ascii=False,
                    )

            # Ejecutar la consulta
            if parametros:
                self.CURSOR.execute(sql, parametros)
            else:
                self.CURSOR.execute(sql)

            # Identificar la operación (SELECT, INSERT, UPDATE, DELETE)
            tipo = sql.strip().split()[0].upper()

            # --- CASO 1: SELECT ---
            if tipo == "SELECT":
                # Extraer los nombres de las columnas
                columnas = [col[0] for col in self.CURSOR.description]

                # Obtener los registros
                registros = self.CURSOR.fetchall()

                resultados = []
                for registro in registros:
                    fila = {}
                    for i, valor in enumerate(registro):
                        fila[columnas[i]] = valor
                    resultados.append(fila)

                return json.dumps(
                    {"estado": True, "Tipo": "SELECT", "registros": resultados},
                    ensure_ascii=False,
                    default=serializador_personalizado,  # Permite convertir fechas a texto JSON
                )

            # --- CASO 2: INSERT, UPDATE, DELETE ---
            else:
                # En PostgreSQL se debe hacer commit() para guardar cambios
                self.CNX.commit()
                filas_afectadas = self.CURSOR.rowcount

                return json.dumps(
                    {
                        "estado": True,
                        "Tipo": tipo,
                        "filas_afectadas": filas_afectadas,
                        "mensaje": f"Operación {tipo} ejecutada exitosamente.",
                    },
                    ensure_ascii=False,
                )

        except psycopg2.Error as e:
            # Si ocurre un error durante un INSERT/UPDATE/DELETE, deshacemos la transacción
            if self.CNX:
                self.CNX.rollback()
            print(f"Error al ejecutar la consulta SQL: {e}")
            return json.dumps(
                {
                    "estado": False,
                    "mensaje": f"Error en la consulta: {e}",
                },
                ensure_ascii=False,
            )

    # ---------------------------------------------------------------------------------------------------------------------------------

    # Método para cerrar la conexión a la base de datos
    def cerrar_conexion(self):
        try:
            if self.CURSOR:
                self.CURSOR.close()
                self.CURSOR = None

            if self.CNX:
                self.CNX.close()
                self.CNX = None

            print(
                f"Conexión cerrada a la base de datos PostgreSQL en {self.HOST}."
            )
            return True
        except psycopg2.Error as e:
            print(
                f"Error al cerrar la conexión a la base de datos PostgreSQL: {self.HOST}"
            )
            print(e)
            return False


# ---------------------------------------------------------------------------------------------------------------------------------
# PRUEBAS DE EJECUCIÓN
# ---------------------------------------------------------------------------------------------------------------------------------

if __name__ == '__main__':
    cnn_postgres = ConexionPostgresql()
    cnn_postgres.crear_conexion()
    sql = """
        SELECT * from Paciente
        """
    parametros = {}
    result = json.loads(cnn_postgres.ejecutar_consulta(sql, parametros))
    cnn_postgres.cerrar_conexion()
    for r in result["registros"]:
        print(r)
        print()
    
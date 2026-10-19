# Sistema de gestión de citas médicas · Centro de Salud de Villamar

Aplicación de escritorio en **Python y PyQt6** para administrar los catálogos (tablas maestras) de un sistema de citas médicas. Funciona con **SQL Server** y con **PostgreSQL**, y sigue la identidad gráfica del Gobierno del Estado de Michoacán.

Proyecto académico · Instituto Tecnológico de Jiquilpan · Ing. en Sistemas Computacionales.

## Características

- **Menú principal** con la opción **Catálogos**, que abre el CRUD de cada tabla maestra: Pacientes, Médicos, Consultorios, Padecimientos, Roles y Permisos.
- **CRUD completo** en cada catálogo: Insertar, Actualizar, Eliminar y Consultar (por Id).
- **Validaciones** antes de enviar los datos a la base: campos obligatorios, teléfono de 10 dígitos, código postal de 5 dígitos, cédula de 7 u 8 dígitos y fecha de nacimiento válida.
- **Mensajes claros** cuando la base rechaza un dato (por ejemplo, una cédula repetida) o cuando no se puede eliminar un registro que otra tabla está usando.
- **Dos motores de base de datos**, que se cambian desde el menú *Base de datos*.
- **Pantalla de inicio** con una tarjeta por catálogo y su cantidad de registros.

## Tecnologías

- Python 3
- PyQt6 (interfaz gráfica)
- `mssql-python` (SQL Server) y `psycopg2` (PostgreSQL)
- `python-dotenv` (configuración con archivo `.env`)

## Estructura del proyecto

```
.
├── main_gui.py               # Ventana principal y menú (punto de entrada)
├── ventanas.py               # Pantallas: inicio, catálogos, formularios
├── repositorio.py            # Todas las consultas SQL del CRUD
├── menu.py                   # Definición de las tablas, validaciones y mensajes de error
├── conexion_sqlserver.py     # Conexión a SQL Server
├── conexion_postgress.py     # Conexión a PostgreSQL
├── tema.py                   # Identidad gráfica (colores, tipografía, estilos)
├── iconos.py                 # Íconos vectoriales y rutas de recursos
├── imagenes/                 # Imagen de inicio e íconos de la app
├── ClinicaVillamar_SQLServer.sql   # Script de la base de datos (SQL Server)
├── ClinicaVillamar_Postgres.sql    # Script de la base de datos (PostgreSQL)
├── requirements.txt
├── .gitignore
└── .env                      # Tus credenciales (NO se sube a GitHub)
```

La interfaz (`ventanas.py`) nunca escribe SQL: llama a `RepositorioCatalogo` (`repositorio.py`), que es la única clase que habla con la base de datos a través de las clases de conexión.

## Requisitos

- Python 3.10 o superior
- SQL Server y/o PostgreSQL instalados y en ejecución
- Controlador ODBC para SQL Server (lo instala `mssql-python`)

## Instalación

1. Clona el repositorio y entra a la carpeta:
   ```bash
   git clone <URL-DEL-REPOSITORIO>
   cd <carpeta-del-repositorio>
   ```
2. Crea y activa un entorno virtual:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate        # Windows
   source .venv/bin/activate     # Linux / macOS
   ```
3. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
   Si `PyQt6` no aparece en el archivo, instálalo con `pip install PyQt6`.

## Configuración (`.env`)

Crea un archivo `.env` en la raíz del proyecto, junto a `main_gui.py`. **No lo subas a GitHub**: contiene tus contraseñas.

```ini
# SQL Server
SERVER_NAME=nombre-del-servidor
DATABASE_NAME=ClinicaVillamar
USER=tu_usuario
PASSWORD=tu_contraseña

# PostgreSQL
PG_HOST=localhost
PG_PORT=5432
PG_DATABASE=ClinicaVillamar
PG_USER=postgres
PG_PASSWORD=tu_contraseña
```

## Base de datos

Los scripts están en la raíz del proyecto e incluyen la creación de las tablas, las restricciones (llaves únicas, `check`, control de citas duplicadas) y los registros de ejemplo.

- **SQL Server:** ejecuta `ClinicaVillamar_SQLServer.sql` en SSMS. El script crea la base de datos.
- **PostgreSQL:** crea primero una base llamada `ClinicaVillamar` y ejecuta `ClinicaVillamar_Postgres.sql` sobre ella.

## Ejecución

```bash
python main_gui.py
```

La aplicación se conecta a SQL Server al abrir. Para usar PostgreSQL, elige **Base de datos → PostgreSQL**.

## Identidad gráfica

La interfaz sigue la [guía gráfica del Gobierno de Michoacán](https://michoacan.gob.mx/guia-grafica/):

- Color guinda `#4A001F` para el texto, y rosa claro `#FFC4D0` y blanco como complementos.
- Logotipo oficial en el encabezado, cargado del CDN oficial al abrir la app (con internet).
- Tipografía Gibson, con una tipografía alterna si no está disponible.
- Pie de página guinda y pleca rosa en el encabezado.

### Personalizar las imágenes

Todo se coloca en la carpeta `imagenes/`:

| Archivo | Uso |
|---|---|
| `fondo_inicio.png` | Imagen de la pantalla de inicio |
| `fondo.jpg` | Tu propia foto para el inicio (sustituye a la anterior, con un velo guinda) |
| `logo_salud.png` | Logotipo de la dependencia, junto al logotipo de Michoacán |
| `icono.ico` | Ícono de la ventana y del ejecutable |

## Aviso sobre logotipos

Los logotipos y la identidad gráfica del Gobierno del Estado de Michoacán y de la Secretaría de Salud pertenecen a sus titulares. Se usan aquí únicamente con fines académicos.

## Autoría

Desarrollado por **María Fernanda Torres Castillo** como parte de la materia de bases de datos del Instituto Tecnológico de Jiquilpan.

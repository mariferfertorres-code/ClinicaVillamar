/* 
   Autor: María Fernanda Torres Castillo 
   Tema: Sistema de gestión de citas médicas - Centro de Salud de Villamar (Estructura Estilizada)
   Fecha: 16 de Septiembre del 2026 
   Modificado: 16 de Octubre del 2026
     - Se agregaron reglas y restricciones (unique, check, default).
     - Se agregó control de duplicidad de citas (médico y consultorio).
     - Se agregó la tabla Evidencia (imágenes y fotografías de la consulta).
     - Se corrigieron los identificadores iniciales (antes Paciente iniciaba en 100
       y Cita en 1000, lo que provocaba errores de llave foránea en los inserts).
*/

-- 1. Tabla Paciente
create table Paciente (
    Id_Paciente serial,
    Nombre varchar(40) not null,
    ApellidoPaterno varchar(40) not null,
    ApellidoMaterno varchar(40),
    FechaNacimiento date not null,
    Genero varchar(15) not null,
    Telefono varchar(15),
    Calle varchar(60) not null,
    Numero varchar(10) not null,
    Colonia varchar(40) not null,
    CodigoPostal varchar(10) not null,
    Ciudad varchar(40) not null,
    constraint pk_Paciente_Id_Paciente primary key(Id_Paciente),
    constraint chk_Paciente_Genero check (Genero in ('Masculino', 'Femenino')),
    constraint chk_Paciente_FechaNacimiento check (FechaNacimiento <= current_date),
    constraint chk_Paciente_Telefono check (Telefono is null or Telefono ~ '^[0-9]{10}$'),
    constraint chk_Paciente_CodigoPostal check (CodigoPostal ~ '^[0-9]{5}$')
);

-- 2. Tabla Medico
create table Medico (
    Id_Medico serial,
    Nombre varchar(40) not null,
    ApellidoPaterno varchar(40) not null,
    Especialidad varchar(40) not null,
    CedulaProfesional varchar(15) not null,
    constraint pk_Medico_Id_Medico primary key(Id_Medico),
    constraint uq_Medico_CedulaProfesional unique (CedulaProfesional),
    constraint chk_Medico_CedulaProfesional check (CedulaProfesional ~ '^[0-9]{7,8}$')
);

-- 3. Tabla Consultorio
create table Consultorio (
    Id_Consultorio serial,
    Numero varchar(10) not null,
    Descripcion varchar(60),
    constraint pk_Consultorio_Id_Consultorio primary key(Id_Consultorio),
    constraint uq_Consultorio_Numero unique (Numero)
);

-- 4. Tabla Padecimiento
create table Padecimiento (
    Id_Padecimiento serial,
    Nombre varchar(80) not null,
    ClaveCIE10 varchar(10) not null,
    Descripcion varchar(200),
    constraint pk_Padecimiento_Id_Padecimiento primary key(Id_Padecimiento),
    constraint uq_Padecimiento_ClaveCIE10 unique (ClaveCIE10)
);

-- 5. Tabla Turno
create table Turno (
    Id_Turno serial,
    Id_Medico integer not null,
    Dia varchar(15) not null,
    HoraInicio time not null,
    HoraFin time not null,
    constraint pk_Turno_Id_Turno primary key(Id_Turno),
    constraint fk_Turno_Id_Medico foreign key(Id_Medico) references Medico(Id_Medico),
    constraint chk_Turno_Dia check (Dia in ('Lunes','Martes','Miercoles','Jueves','Viernes')),
    constraint chk_Turno_Horas check (HoraFin > HoraInicio),
    constraint uq_Turno_Medico_Dia_Hora unique (Id_Medico, Dia, HoraInicio)
);

-- 6. Tabla Rol
create table Rol (
    Id_Rol serial,
    Nombre varchar(30) not null,
    Descripcion varchar(150),
    constraint pk_Rol_Id_Rol primary key(Id_Rol),
    constraint uq_Rol_Nombre unique (Nombre)
);

-- 7. Tabla Permiso
create table Permiso (
    Id_Permiso serial,
    Nombre varchar(40) not null,
    Descripcion varchar(150),
    constraint pk_Permiso_Id_Permiso primary key(Id_Permiso),
    constraint uq_Permiso_Nombre unique (Nombre)
);

-- 8. Tabla Usuario
create table Usuario (
    Id_Usuario serial,
    Id_Rol integer not null,
    NombreUsuario varchar(30) not null,
    Contrasena varchar(30) not null,
    Estado boolean not null default true,
    constraint pk_Usuario_Id_Usuario primary key(Id_Usuario),
    constraint fk_Usuario_Id_Rol foreign key(Id_Rol) references Rol(Id_Rol),
    constraint uq_Usuario_NombreUsuario unique (NombreUsuario),
    constraint chk_Usuario_Contrasena check (length(Contrasena) >= 8)
);

-- 9. Tabla RolPermiso
create table RolPermiso (
    Id_RolPermiso serial,
    Id_Rol integer not null,
    Id_Permiso integer not null,
    Estado boolean not null default true,
    constraint pk_RolPermiso_Id_RolPermiso primary key(Id_RolPermiso),
    constraint fk_RolPermiso_Id_Rol foreign key(Id_Rol) references Rol(Id_Rol),
    constraint fk_RolPermiso_Id_Permiso foreign key(Id_Permiso) references Permiso(Id_Permiso),
    constraint uq_RolPermiso_Rol_Permiso unique (Id_Rol, Id_Permiso)
);

-- 10. Tabla Cita
create table Cita (
    Id_Cita serial,
    Id_Paciente integer not null,
    Id_Medico integer not null,
    Id_Turno integer not null,
    Id_Consultorio integer not null,
    Id_Usuario integer not null,
    Fecha date not null,
    Hora time not null,
    Estado varchar(15) not null default 'Agendada',
    constraint pk_Cita_Id_Cita primary key(Id_Cita),
    constraint fk_Cita_Id_Paciente foreign key(Id_Paciente) references Paciente(Id_Paciente),
    constraint fk_Cita_Id_Medico foreign key(Id_Medico) references Medico(Id_Medico),
    constraint fk_Cita_Id_Turno foreign key(Id_Turno) references Turno(Id_Turno),
    constraint fk_Cita_Id_Consultorio foreign key(Id_Consultorio) references Consultorio(Id_Consultorio),
    constraint fk_Cita_Id_Usuario foreign key(Id_Usuario) references Usuario(Id_Usuario),
    constraint chk_Cita_Estado check (Estado in ('Agendada', 'Atendida', 'Cancelada'))
);

-- Control de concurrencia: no se permiten dos citas activas en el mismo
-- horario para el mismo médico ni para el mismo consultorio.
-- Las citas canceladas quedan excluidas para poder reagendar ese horario.
create unique index uq_Cita_Medico_Horario
    on Cita(Id_Medico, Fecha, Hora) where Estado <> 'Cancelada';

create unique index uq_Cita_Consultorio_Horario
    on Cita(Id_Consultorio, Fecha, Hora) where Estado <> 'Cancelada';

-- 11. Tabla DetalleCita
create table DetalleCita (
    Id_DetalleCita serial,
    Id_Cita integer not null,
    Id_Padecimiento integer not null,
    TipoConsulta varchar(15) not null,
    Observaciones varchar(250),
    constraint pk_DetalleCita_Id_DetalleCita primary key(Id_DetalleCita),
    constraint fk_DetalleCita_Id_Cita foreign key(Id_Cita) references Cita(Id_Cita),
    constraint fk_DetalleCita_Id_Padecimiento foreign key(Id_Padecimiento) references Padecimiento(Id_Padecimiento),
    constraint chk_DetalleCita_TipoConsulta check (TipoConsulta in ('Primera vez','Subsecuente')),
    constraint uq_DetalleCita_Cita_Padecimiento unique (Id_Cita, Id_Padecimiento)
);

-- 12. Tabla Evidencia (imágenes y fotografías de la consulta)
create table Evidencia (
    Id_Evidencia serial,
    Id_DetalleCita integer not null,
    NombreArchivo varchar(100) not null,
    TipoArchivo varchar(10) not null,
    Ruta varchar(260) not null,
    Descripcion varchar(150),
    FechaRegistro timestamp not null default current_timestamp,
    constraint pk_Evidencia_Id_Evidencia primary key(Id_Evidencia),
    constraint fk_Evidencia_Id_DetalleCita foreign key(Id_DetalleCita) references DetalleCita(Id_DetalleCita),
    constraint chk_Evidencia_TipoArchivo check (TipoArchivo in ('jpg','jpeg','png')),
    constraint uq_Evidencia_Ruta unique (Ruta)
);

-- PUNTO 3: INSERCIÓN DE INFORMACIÓN

-- ---------- Paciente (5) ----------
insert into Paciente (Nombre, ApellidoPaterno, ApellidoMaterno, FechaNacimiento, Genero, Telefono, Calle, Numero, Colonia, CodigoPostal, Ciudad) values
('Maria Guadalupe', 'Torres', 'Castillo', '1990-05-14', 'Femenino', '3531120045', 'Hidalgo', '112', 'Centro', '59510', 'Villamar'),
('Juan Carlos', 'Ramirez', 'Lopez', '1985-11-02', 'Masculino', '3531120078', 'Morelos', '45', 'La Loma', '59510', 'Villamar'),
('Sofia', 'Hernandez', 'Morales', '2019-03-22', 'Femenino', '3531120099', 'Independencia', '23', 'Centro', '59510', 'Villamar'),
('Miguel Angel', 'Chavez', 'Ibarra', '2020-07-09', 'Masculino', '3531120150', 'Zaragoza', '8', 'San Isidro', '59510', 'Villamar'),
('Fernanda', 'Rodriguez', 'Silva', '1996-01-30', 'Femenino', '3531120187', 'Aldama', '76', 'Centro', '59510', 'Villamar');

-- ---------- Medico (5) ----------
insert into Medico (Nombre, ApellidoPaterno, Especialidad, CedulaProfesional) values
('Alejandra', 'Mendoza Ruiz', 'Medicina General', '8452193'),
('Roberto', 'Gomez Castillo', 'Medicina General', '7891234'),
('Lucia', 'Fernandez Torres', 'Pediatria', '6234567'),
('Jorge', 'Salazar Nunez', 'Medicina Interna', '5678901'),
('Mariana', 'Ortiz Vega', 'Ginecologia', '9012345');

-- ---------- Consultorio (5) ----------
insert into Consultorio (Numero, Descripcion) values
('1', 'Medicina General'),
('2', 'Medicina General'),
('3', 'Pediatria'),
('4', 'Medicina Interna'),
('5', 'Ginecologia');

-- ---------- Padecimiento (5) ----------
insert into Padecimiento (Nombre, ClaveCIE10, Descripcion) values
('Diabetes mellitus tipo 2', 'E11', 'Trastorno metabolico caracterizado por niveles elevados de glucosa en sangre.'),
('Hipertension arterial', 'I10', 'Presion arterial elevada de forma sostenida.'),
('Infeccion de vias respiratorias superiores', 'J06.9', 'Cuadro respiratorio agudo que afecta nariz, garganta o vias altas.'),
('Gastroenteritis aguda', 'A09', 'Inflamacion del tracto digestivo con diarrea y/o vomito.'),
('Control prenatal', 'Z34.9', 'Supervision de un embarazo normal.');

-- ---------- Rol (5) ----------
insert into Rol (Nombre, Descripcion) values
('Administrador', 'Control total del sistema, incluida la gestion de usuarios.'),
('Recepcionista', 'Encargado de agendar, reagendar y cancelar citas.'),
('Medico', 'Consulta su agenda y registra el detalle de la consulta.'),
('Enfermeria', 'Apoyo en la preparacion de consultas y signos vitales.'),
('Jefatura', 'Supervisa la disponibilidad de horarios y genera reportes.');

-- ---------- Permiso (5) ----------
insert into Permiso (Nombre, Descripcion) values
('Registrar cita', 'Permite capturar una nueva cita medica.'),
('Cancelar cita', 'Permite cancelar o reagendar una cita existente.'),
('Consultar disponibilidad', 'Permite ver los horarios disponibles por medico.'),
('Gestionar usuarios', 'Permite crear, editar o desactivar usuarios del sistema.'),
('Generar reportes', 'Permite generar reportes de consultas y padecimientos.');

-- ---------- Usuario (5) ----------
insert into Usuario (Id_Rol, NombreUsuario, Contrasena, Estado) values
(1, 'admin1', 'Admin2026*', true),
(2, 'recep1', 'Recep2026*', true),
(2, 'recep2', 'Recep2026#', true),
(3, 'dra.mendoza', 'Medico2026*', true),
(5, 'jefatura1', 'Jefa2026*', true);

-- ---------- Turno (10) ----------
insert into Turno (Id_Medico, Dia, HoraInicio, HoraFin) values
(1, 'Lunes', '08:00', '14:00'),
(1, 'Miercoles', '08:00', '14:00'),
(2, 'Martes', '08:00', '14:00'),
(2, 'Jueves', '08:00', '14:00'),
(3, 'Lunes', '09:00', '13:00'),
(3, 'Viernes', '09:00', '13:00'),
(4, 'Miercoles', '10:00', '15:00'),
(5, 'Martes', '10:00', '15:00'),
(5, 'Jueves', '10:00', '15:00'),
(5, 'Viernes', '10:00', '13:00');

-- ---------- RolPermiso (10) ----------
insert into RolPermiso (Id_Rol, Id_Permiso, Estado) values
(1, 1, true), (1, 2, true), (1, 4, true), (1, 5, true),   -- Administrador
(2, 1, true), (2, 2, true), (2, 3, true),                 -- Recepcionista
(3, 3, true), (3, 5, true),                               -- Medico
(5, 5, true);                                             -- Jefatura

-- ---------- Cita (10) ----------
insert into Cita (Id_Paciente, Id_Medico, Id_Turno, Id_Consultorio, Id_Usuario, Fecha, Hora, Estado) values
(1, 1, 1, 1, 2, '2026-09-07', '08:30', 'Atendida'),
(2, 1, 2, 1, 2, '2026-09-09', '09:00', 'Atendida'),
(3, 3, 5, 3, 3, '2026-09-07', '10:00', 'Atendida'),
(4, 2, 3, 2, 2, '2026-09-08', '09:00', 'Agendada'),
(5, 5, 8, 5, 3, '2026-09-08', '11:00', 'Atendida'),
(1, 4, 7, 4, 2, '2026-09-09', '11:00', 'Atendida'),
(2, 5, 9, 5, 3, '2026-09-10', '10:30', 'Cancelada'),
(3, 1, 1, 1, 2, '2026-09-14', '08:00', 'Agendada'),
(4, 3, 6, 3, 3, '2026-09-11', '09:30', 'Atendida'),
(5, 2, 4, 2, 2, '2026-09-10', '09:00', 'Atendida');

-- ---------- DetalleCita (10) ----------
insert into DetalleCita (Id_Cita, Id_Padecimiento, TipoConsulta, Observaciones) values
(1, 2, 'Subsecuente', 'Paciente en control, presion arterial estable.'),
(1, 3, 'Primera vez', 'Refiere congestion nasal y tos leve de 3 dias de evolucion.'),
(2, 3, 'Primera vez', 'Fiebre de 38 grados y dolor de garganta.'),
(3, 3, 'Primera vez', 'Tos con flemas, sin fiebre.'),
(3, 4, 'Primera vez', 'Presenta ademas evacuaciones liquidas desde ayer.'),
(5, 5, 'Subsecuente', 'Semana 28 de gestacion, sin complicaciones.'),
(6, 1, 'Subsecuente', 'Glucosa en ayuno de 145 mg/dL, se ajusta tratamiento.'),
(6, 2, 'Subsecuente', 'Presion arterial 140/90, se mantiene tratamiento actual.'),
(9, 4, 'Primera vez', 'Vomito y diarrea de 2 dias de evolucion.'),
(10, 3, 'Subsecuente', 'Persiste tos leve, mejoria notable.');

-- ---------- Evidencia (10) ----------
insert into Evidencia (Id_DetalleCita, NombreArchivo, TipoArchivo, Ruta, Descripcion, FechaRegistro) values
(1, 'presion_arterial_01.jpg', 'jpg', 'evidencias/2026-09-07/presion_arterial_01.jpg', 'Fotografia del registro de presion arterial.', '2026-09-07 08:45'),
(2, 'garganta_01.jpg', 'jpg', 'evidencias/2026-09-07/garganta_01.jpg', 'Fotografia de la garganta del paciente.', '2026-09-07 08:50'),
(3, 'garganta_02.jpg', 'jpg', 'evidencias/2026-09-09/garganta_02.jpg', 'Fotografia de la garganta con inflamacion.', '2026-09-09 09:15'),
(4, 'receta_tos_01.png', 'png', 'evidencias/2026-09-07/receta_tos_01.png', 'Imagen de la receta indicada.', '2026-09-07 10:20'),
(5, 'hidratacion_01.jpg', 'jpg', 'evidencias/2026-09-07/hidratacion_01.jpg', 'Fotografia del suero oral indicado.', '2026-09-07 10:25'),
(6, 'ultrasonido_01.png', 'png', 'evidencias/2026-09-08/ultrasonido_01.png', 'Imagen del ultrasonido de control prenatal.', '2026-09-08 11:30'),
(7, 'glucosa_01.jpg', 'jpg', 'evidencias/2026-09-09/glucosa_01.jpg', 'Fotografia del resultado de glucosa en ayuno.', '2026-09-09 11:20'),
(8, 'presion_arterial_02.jpg', 'jpg', 'evidencias/2026-09-09/presion_arterial_02.jpg', 'Fotografia de la toma de presion arterial.', '2026-09-09 11:25'),
(9, 'deshidratacion_01.jpg', 'jpg', 'evidencias/2026-09-11/deshidratacion_01.jpg', 'Fotografia de signos de deshidratacion leve.', '2026-09-11 09:50'),
(10, 'receta_respiratoria_01.png', 'png', 'evidencias/2026-09-10/receta_respiratoria_01.png', 'Imagen de la receta de seguimiento.', '2026-09-10 09:20');

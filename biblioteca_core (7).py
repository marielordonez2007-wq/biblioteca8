import json
import os
import secrets
import string
import hashlib
import sqlite3
import re
from datetime import date, timedelta


# ============================================================
# CONFIGURACION GENERAL
# ============================================================

ARCHIVO_DATOS = "biblioteca.db"
DIAS_PRESTAMO = 7
MAX_LIBROS = 5

PREGUNTAS_SEGURIDAD = [
    "Cual es el nombre de tu primera mascota?",
    "Cual es tu comida favorita?",
    "Cual es el nombre de tu mejor amigo de infancia?",
    "Cual es tu lugar favorito?",
    "Cual era tu materia favorita en la escuela?",
]


# ============================================================
# DATOS INICIALES
# ============================================================

LIBROS_INICIALES = [
    {
        "id": 1,
        "titulo": "Batman: Year One",
        "autor": "Frank Miller",
        "genero": "Novela grafica",
        "stock": 2,
        "origen": "Compra",
        "fecha_alta": "2026-01-01",
    },
    {
        "id": 2,
        "titulo": "Resident Evil Archives",
        "autor": "Capcom",
        "genero": "Terror",
        "stock": 2,
        "origen": "Compra",
        "fecha_alta": "2026-01-01",
    },
    {
        "id": 3,
        "titulo": "El arte de crear",
        "autor": "Autor desconocido",
        "genero": "Creatividad",
        "stock": 2,
        "origen": "Donacion",
        "fecha_alta": "2026-01-01",
    },
    {
        "id": 4,
        "titulo": "El Principito",
        "autor": "Antoine de Saint-Exupery",
        "genero": "Literatura",
        "stock": 2,
        "origen": "Donacion",
        "fecha_alta": "2026-01-01",
    },
    {
        "id": 5,
        "titulo": "El Arte de la Guerra",
        "autor": "Sun Tzu",
        "genero": "Estrategia",
        "stock": 2,
        "origen": "Compra",
        "fecha_alta": "2026-01-01",
    },
    {
        "id": 6,
        "titulo": "Cien Anos de Soledad",
        "autor": "Gabriel Garcia Marquez",
        "genero": "Realismo magico",
        "stock": 2,
        "origen": "Compra",
        "fecha_alta": "2026-01-01",
    },
    {
        "id": 7,
        "titulo": "Don Quijote",
        "autor": "Miguel de Cervantes",
        "genero": "Clasico",
        "stock": 2,
        "origen": "Donacion",
        "fecha_alta": "2026-01-01",
    },
    {
        "id": 8,
        "titulo": "1984",
        "autor": "George Orwell",
        "genero": "Distopia",
        "stock": 2,
        "origen": "Compra",
        "fecha_alta": "2026-01-01",
    },
    {
        "id": 9,
        "titulo": "Fahrenheit 451",
        "autor": "Ray Bradbury",
        "genero": "Ciencia ficcion",
        "stock": 2,
        "origen": "Intercambio",
        "fecha_alta": "2026-01-01",
    },
    {
        "id": 10,
        "titulo": "Dracula",
        "autor": "Bram Stoker",
        "genero": "Terror",
        "stock": 2,
        "origen": "Compra",
        "fecha_alta": "2026-01-01",
    },
]


GENEROS_PREDETERMINADOS = [
    "Literatura",
    "Romance",
    "Misterio",
    "Terror",
    "Fantasia",
    "Ciencia ficcion",
    "Aventura",
    "Drama",
    "Comedia",
    "Historia",
    "Suspenso",
    "Infantil",
]

MAPA_GENEROS_ANTIGUOS = {
    "novela grafica": "Literatura",
    "creatividad": "Literatura",
    "estrategia": "Aventura",
    "realismo magico": "Literatura",
    "clasico": "Literatura",
    "distopia": "Ciencia ficcion",
}

USUARIOS_INICIALES = [
    {
        "nombre": "Neithan Durant",
        "usuario": "@neithan",
        "codigo": "1234",
        "telefono": "99999999",
        "rol": "CLIENTE",
        "password": "1234",
        "deuda": 200,
        "pagado": 0,
    },
    {
        "nombre": "Jose Carranza",
        "usuario": "@jose",
        "codigo": "1010",
        "telefono": "88888888",
        "rol": "CLIENTE",
        "password": "1010",
        "deuda": 100,
        "pagado": 0,
    },
    {
        "nombre": "Administrador",
        "usuario": "@admin",
        "codigo": "admin",
        "telefono": "00000000",
        "rol": "ADMIN",
        "password": "Admin123!",
        "deuda": 0,
        "pagado": 0,
    },
]


# ============================================================
# FUNCIONES DE SEGURIDAD Y UTILIDAD
# ============================================================

def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()



def hoy_texto():
    return date.today().isoformat()


def fecha_legible(valor):
    try:
        return date.fromisoformat(valor).strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        return valor


# ============================================================
# CLASE PRINCIPAL: LOGICA Y PERSISTENCIA
# ============================================================

class Biblioteca:
    """Capa de datos de la biblioteca usando SQLite."""

    def __init__(self):
        self.con = sqlite3.connect(ARCHIVO_DATOS, check_same_thread=False)
        self.con.row_factory = sqlite3.Row
        self.crear_tablas()
        if self.base_vacia():
            self.datos_iniciales()
        self.normalizar_generos()
        self.asegurar_administrador()
        self.asegurar_multas_demo()
        self.actualizar_multas_vencidas()
        self.refrescar_cache()

    # --------------------------------------------------------
    # BASE DE DATOS
    # --------------------------------------------------------

    def crear_tablas(self):
        self.con.executescript("""
        PRAGMA foreign_keys = ON;

        CREATE TABLE IF NOT EXISTS usuarios (
            codigo TEXT PRIMARY KEY,
            usuario TEXT UNIQUE,
            nombre TEXT NOT NULL,
            telefono TEXT NOT NULL UNIQUE,
            rol TEXT NOT NULL CHECK (rol IN ('CLIENTE', 'ADMIN')),
            password TEXT NOT NULL,
            deuda REAL NOT NULL DEFAULT 0 CHECK (deuda >= 0),
            pagado REAL NOT NULL DEFAULT 0 CHECK (pagado >= 0),
            pregunta_seguridad TEXT DEFAULT '',
            respuesta_seguridad TEXT DEFAULT '',
            pregunta_seguridad_2 TEXT DEFAULT '',
            respuesta_seguridad_2 TEXT DEFAULT '',
            pregunta_seguridad_3 TEXT DEFAULT '',
            respuesta_seguridad_3 TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS libros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            autor TEXT NOT NULL,
            genero TEXT NOT NULL,
            stock INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
            origen TEXT NOT NULL,
            fecha_alta TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS prestamos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_usuario TEXT NOT NULL,
            id_libro INTEGER NOT NULL,
            fecha_prestamo TEXT NOT NULL,
            fecha_vencimiento TEXT NOT NULL,
            fecha_devolucion TEXT DEFAULT '',
            estado TEXT NOT NULL DEFAULT 'PRESTADO' CHECK (estado IN ('PRESTADO', 'DEVUELTO')),
            multa REAL NOT NULL DEFAULT 0,
            multa_pagada INTEGER NOT NULL DEFAULT 0 CHECK (multa_pagada IN (0, 1)),
            FOREIGN KEY (codigo_usuario) REFERENCES usuarios(codigo) ON UPDATE CASCADE ON DELETE RESTRICT,
            FOREIGN KEY (id_libro) REFERENCES libros(id) ON DELETE RESTRICT
        );

        CREATE TABLE IF NOT EXISTS solicitudes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_usuario TEXT NOT NULL,
            id_libro INTEGER DEFAULT NULL,
            tipo TEXT NOT NULL,
            titulo TEXT NOT NULL,
            autor TEXT DEFAULT '',
            genero TEXT DEFAULT '',
            comentario TEXT DEFAULT '',
            estado TEXT NOT NULL DEFAULT 'PENDIENTE' CHECK (estado IN ('PENDIENTE', 'APROBADA', 'RECHAZADA')),
            fecha TEXT NOT NULL,
            FOREIGN KEY (codigo_usuario) REFERENCES usuarios(codigo) ON UPDATE CASCADE ON DELETE RESTRICT
        );

        CREATE TABLE IF NOT EXISTS movimientos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            tipo TEXT NOT NULL,
            detalle TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS configuracion (
            clave TEXT PRIMARY KEY,
            valor TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS calificaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_usuario TEXT NOT NULL,
            id_libro INTEGER NOT NULL,
            calificacion INTEGER NOT NULL CHECK (calificacion BETWEEN 1 AND 5),
            comentario TEXT DEFAULT '',
            fecha TEXT NOT NULL,
            UNIQUE(codigo_usuario, id_libro),
            FOREIGN KEY (codigo_usuario) REFERENCES usuarios(codigo) ON UPDATE CASCADE ON DELETE RESTRICT,
            FOREIGN KEY (id_libro) REFERENCES libros(id) ON DELETE RESTRICT
        );

        CREATE INDEX IF NOT EXISTS idx_calificaciones_libro ON calificaciones(id_libro);
        CREATE INDEX IF NOT EXISTS idx_calificaciones_usuario ON calificaciones(codigo_usuario);

        CREATE INDEX IF NOT EXISTS idx_libros_titulo ON libros(titulo);
        CREATE INDEX IF NOT EXISTS idx_libros_autor ON libros(autor);
        CREATE INDEX IF NOT EXISTS idx_libros_genero ON libros(genero);
        CREATE INDEX IF NOT EXISTS idx_prestamos_usuario ON prestamos(codigo_usuario);
        CREATE INDEX IF NOT EXISTS idx_prestamos_libro ON prestamos(id_libro);
        CREATE INDEX IF NOT EXISTS idx_solicitudes_usuario ON solicitudes(codigo_usuario);

        CREATE UNIQUE INDEX IF NOT EXISTS idx_prestamo_activo_unico
            ON prestamos(codigo_usuario, id_libro)
            WHERE estado = 'PRESTADO';
        """)
        # Migracion para bases de datos creadas con versiones anteriores.
        columnas = {fila["name"] for fila in self.con.execute("PRAGMA table_info(usuarios)")}
        if "pregunta_seguridad" not in columnas:
            self.con.execute("ALTER TABLE usuarios ADD COLUMN pregunta_seguridad TEXT DEFAULT ''")
        if "respuesta_seguridad" not in columnas:
            self.con.execute("ALTER TABLE usuarios ADD COLUMN respuesta_seguridad TEXT DEFAULT ''")
        if "usuario" not in columnas:
            self.con.execute("ALTER TABLE usuarios ADD COLUMN usuario TEXT")
        if "pregunta_seguridad_2" not in columnas:
            self.con.execute("ALTER TABLE usuarios ADD COLUMN pregunta_seguridad_2 TEXT DEFAULT ''")
        if "respuesta_seguridad_2" not in columnas:
            self.con.execute("ALTER TABLE usuarios ADD COLUMN respuesta_seguridad_2 TEXT DEFAULT ''")
        if "pregunta_seguridad_3" not in columnas:
            self.con.execute("ALTER TABLE usuarios ADD COLUMN pregunta_seguridad_3 TEXT DEFAULT ''")
        if "respuesta_seguridad_3" not in columnas:
            self.con.execute("ALTER TABLE usuarios ADD COLUMN respuesta_seguridad_3 TEXT DEFAULT ''")

        # Asignar nombres de usuario a cuentas antiguas sin alterar sus prestamos/historial.
        usuarios_sin_login = self.con.execute(
            "SELECT codigo, nombre FROM usuarios WHERE usuario IS NULL OR trim(usuario) = ''"
        ).fetchall()
        for fila in usuarios_sin_login:
            base = re.sub(r"[^a-z0-9]", "", fila["nombre"].lower().replace(" ", "")) or "usuario"
            base = "@" + base
            candidato = base
            numero = 2
            while self.con.execute("SELECT 1 FROM usuarios WHERE lower(usuario) = lower(?)", (candidato,)).fetchone():
                candidato = f"{base}{numero}"
                numero += 1
            self.con.execute("UPDATE usuarios SET usuario = ? WHERE codigo = ?", (candidato, fila["codigo"]))

        # Las cuentas existentes pasan al nuevo formato @usuario.
        usuarios_sin_arroba = self.con.execute(
            "SELECT codigo, usuario FROM usuarios WHERE usuario IS NOT NULL AND trim(usuario) != '' AND substr(trim(usuario), 1, 1) != '@'"
        ).fetchall()
        for fila in usuarios_sin_arroba:
            candidato = "@" + re.sub(r"[^a-zA-Z0-9_.-]", "", fila["usuario"].strip())
            if not re.fullmatch(r"@[a-zA-Z0-9_.-]{3,20}", candidato):
                continue
            existe = self.con.execute(
                "SELECT codigo FROM usuarios WHERE lower(usuario) = lower(?) AND codigo != ? LIMIT 1",
                (candidato, fila["codigo"])
            ).fetchone()
            if existe:
                base = candidato
                numero = 2
                while self.con.execute("SELECT 1 FROM usuarios WHERE lower(usuario) = lower(?)", (f"{base}{numero}",)).fetchone():
                    numero += 1
                candidato = f"{base}{numero}"
            self.con.execute("UPDATE usuarios SET usuario = ? WHERE codigo = ?", (candidato, fila["codigo"]))

        # Cuentas antiguas: conservar la pregunta/respuesta anterior como primera pregunta.
        # El sistema actual utiliza solamente dos preguntas de seguridad.
        self.con.execute(
            "UPDATE usuarios SET pregunta_seguridad_2 = ? "
            "WHERE trim(pregunta_seguridad_2) = ''",
            (PREGUNTAS_SEGURIDAD[1],)
        )
        self.con.execute(
            "UPDATE usuarios SET respuesta_seguridad_2 = respuesta_seguridad "
            "WHERE trim(respuesta_seguridad_2) = '' AND trim(respuesta_seguridad) != ''"
        )

        columnas = {fila["name"] for fila in self.con.execute("PRAGMA table_info(solicitudes)")}
        if "id_libro" not in columnas:
            self.con.execute("ALTER TABLE solicitudes ADD COLUMN id_libro INTEGER DEFAULT NULL")
        if "comentario" not in columnas:
            self.con.execute("ALTER TABLE solicitudes ADD COLUMN comentario TEXT DEFAULT ''")

        # Normalizamos los generos antiguos para que el sistema trabaje
        # solamente con las categorias permitidas.
        for antiguo, nuevo in MAPA_GENEROS_ANTIGUOS.items():
            self.con.execute(
                "UPDATE libros SET genero = ? WHERE lower(genero) = ?",
                (nuevo, antiguo)
            )
        placeholders = ",".join("?" for _ in GENEROS_PREDETERMINADOS)
        self.con.execute(
            f"UPDATE libros SET genero = 'Literatura' WHERE genero NOT IN ({placeholders})",
            GENEROS_PREDETERMINADOS
        )
        self.con.commit()

    def normalizar_generos(self):
        """Convierte categorias antiguas a las categorias oficiales del sistema."""
        for antiguo, nuevo in MAPA_GENEROS_ANTIGUOS.items():
            self.con.execute(
                "UPDATE libros SET genero = ? WHERE lower(genero) = ?",
                (nuevo, antiguo)
            )
        placeholders = ",".join("?" for _ in GENEROS_PREDETERMINADOS)
        self.con.execute(
            f"UPDATE libros SET genero = 'Literatura' WHERE genero NOT IN ({placeholders})",
            GENEROS_PREDETERMINADOS
        )
        self.con.commit()

    def asegurar_administrador(self):
        fila = self.con.execute(
            "SELECT codigo, rol FROM usuarios WHERE lower(usuario) IN ('admin', '@admin') OR lower(codigo) = 'admin' LIMIT 1"
        ).fetchone()

        if fila is None:
            self.con.execute(
                """INSERT INTO usuarios
                   (codigo, usuario, nombre, telefono, rol, password, deuda, pagado,
                    pregunta_seguridad, respuesta_seguridad, pregunta_seguridad_2, respuesta_seguridad_2,
                    pregunta_seguridad_3, respuesta_seguridad_3)
                   VALUES ('admin', '@admin', 'Administrador', '00000000', 'ADMIN', ?, 0, 0, ?, ?, ?, ?, ?, ?)""",
                (
                    hash_password("Admin123!"),
                    PREGUNTAS_SEGURIDAD[0], hash_password("biblioteca"),
                    PREGUNTAS_SEGURIDAD[1], hash_password("libro"),
                    PREGUNTAS_SEGURIDAD[2], hash_password("lectura")
                )
            )
            self.con.commit()
        else:
            self.con.execute("UPDATE usuarios SET usuario = '@admin' WHERE codigo = ?", (fila["codigo"],))
            self.con.commit()

    def asegurar_multas_demo(self):
        """Carga una sola vez deudas de demostracion para los usuarios de prueba.
        No vuelve a agregarlas despues de que hayan sido pagadas.
        """
        fila = self.con.execute("SELECT valor FROM configuracion WHERE clave = 'multas_demo_cargadas'").fetchone()
        if fila:
            return
        cambios = False
        for nombre_usuario, monto in (("@neithan", 200.0), ("@jose", 100.0)):
            usuario = self.buscar_usuario_login(nombre_usuario) if hasattr(self, 'con') else None
            if usuario and float(usuario["deuda"] or 0) <= 0.000001 and float(usuario["pagado"] or 0) <= 0.000001:
                self.con.execute("UPDATE usuarios SET deuda = ? WHERE usuario = ?", (monto, nombre_usuario))
                self.registrar_movimiento("MULTA", f"Se cargo una deuda demo de L.{monto:.2f} a {usuario['nombre']}.")
                cambios = True
        self.con.execute("INSERT INTO configuracion (clave, valor) VALUES ('multas_demo_cargadas', '1')")
        if cambios:
            self.con.commit()

    def base_vacia(self):
        fila = self.con.execute("SELECT COUNT(*) AS total FROM usuarios").fetchone()
        return fila["total"] == 0

    def actualizar_multas_vencidas(self):
        """Actualiza automaticamente la multa acumulada de prestamos aun no devueltos.
        El plazo es de 7 dias. Solo se suma a la deuda el incremento que aun no
        estaba registrado, evitando cobrar dos veces por el mismo dia.
        """
        hoy = date.today()
        prestamos = self.con.execute(
            """SELECT id, codigo_usuario, fecha_vencimiento, multa, estado
               FROM prestamos WHERE estado = 'PRESTADO'"""
        ).fetchall()
        cambios = False
        for fila in prestamos:
            vencimiento = date.fromisoformat(fila["fecha_vencimiento"])
            dias_atraso = max((hoy - vencimiento).days, 0)
            if dias_atraso <= 0:
                continue
            multa_esperada = dias_atraso * self.obtener_multa_por_dia()
            multa_actual = float(fila["multa"] or 0)
            incremento = max(multa_esperada - multa_actual, 0)
            if incremento > 0.000001:
                self.con.execute(
                    "UPDATE prestamos SET multa = ?, multa_pagada = 0 WHERE id = ?",
                    (multa_esperada, fila["id"])
                )
                self.con.execute(
                    "UPDATE usuarios SET deuda = deuda + ? WHERE codigo = ?",
                    (incremento, fila["codigo_usuario"])
                )
                cambios = True
                self.registrar_movimiento(
                    "MULTA",
                    f"Se acumulo L.{incremento:.2f} de multa por atraso en el prestamo #{fila['id']}."
                )
        if cambios:
            self.con.commit()

    def refrescar_cache(self):
        self.libros = [dict(f) for f in self.con.execute("SELECT id, titulo, autor, genero, stock, origen, fecha_alta FROM libros ORDER BY id")]
        self.usuarios = [dict(f) for f in self.con.execute("SELECT codigo, usuario, nombre, telefono, rol, password, deuda, pagado, pregunta_seguridad, respuesta_seguridad, pregunta_seguridad_2, respuesta_seguridad_2, pregunta_seguridad_3, respuesta_seguridad_3 FROM usuarios ORDER BY nombre")]
        self.prestamos = [dict(f) for f in self.con.execute("SELECT id, codigo_usuario, id_libro, fecha_prestamo, fecha_vencimiento, fecha_devolucion, estado, multa, multa_pagada FROM prestamos ORDER BY id")]
        for p in self.prestamos:
            p["multa_pagada"] = bool(p["multa_pagada"])
        self.solicitudes = [dict(f) for f in self.con.execute("SELECT id, codigo_usuario, id_libro, tipo, titulo, autor, genero, comentario, estado, fecha FROM solicitudes ORDER BY id")]
        self.movimientos = [dict(f) for f in self.con.execute("SELECT fecha, tipo, detalle FROM movimientos ORDER BY id")]
        self.calificaciones = [dict(f) for f in self.con.execute(
            "SELECT id, codigo_usuario, id_libro, calificacion, comentario, fecha "
            "FROM calificaciones ORDER BY id"
        )]

    def puede_calificar(self, codigo_usuario, libro_id):
        # Solo puede calificar quien haya tenido el libro y ya lo haya devuelto.
        fila = self.con.execute(
            """SELECT 1 FROM prestamos
               WHERE codigo_usuario = ? AND id_libro = ? AND estado = 'DEVUELTO'
               LIMIT 1""",
            (codigo_usuario, libro_id)
        ).fetchone()
        return fila is not None

    def obtener_calificacion_usuario(self, codigo_usuario, libro_id):
        fila = self.con.execute(
            """SELECT id, codigo_usuario, id_libro, calificacion, comentario, fecha
               FROM calificaciones
               WHERE codigo_usuario = ? AND id_libro = ?
               LIMIT 1""",
            (codigo_usuario, libro_id)
        ).fetchone()
        return dict(fila) if fila else None

    def guardar_calificacion(self, codigo_usuario, libro_id, calificacion, comentario):
        if not self.puede_calificar(codigo_usuario, libro_id):
            return False, "Solo puede calificar un libro que haya tomado en prestamo y devuelto."

        if not 1 <= int(calificacion) <= 5:
            return False, "La calificacion debe estar entre 1 y 5."

        comentario = comentario.strip()

        try:
            self.con.execute(
                """INSERT INTO calificaciones
                   (codigo_usuario, id_libro, calificacion, comentario, fecha)
                   VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT(codigo_usuario, id_libro)
                   DO UPDATE SET calificacion=excluded.calificacion,
                                 comentario=excluded.comentario,
                                 fecha=excluded.fecha""",
                (codigo_usuario, libro_id, int(calificacion), comentario, hoy_texto())
            )
            libro = self.buscar_libro(libro_id)
            titulo = libro["titulo"] if libro else "Desconocido"
            self.registrar_movimiento(
                "CALIFICACION",
                f"{codigo_usuario} califico '{titulo}' con {int(calificacion)}/5."
            )
            self.con.commit()
            self.refrescar_cache()
            return True, "Calificacion guardada correctamente."
        except sqlite3.Error:
            self.con.rollback()
            return False, "No se pudo guardar la calificacion."

    def opiniones_libro(self, libro_id):
        filas = self.con.execute(
            """SELECT c.calificacion, c.comentario, c.fecha,
                      u.nombre, u.codigo
               FROM calificaciones c
               JOIN usuarios u ON u.codigo = c.codigo_usuario
               WHERE c.id_libro = ?
               ORDER BY c.id DESC""",
            (libro_id,)
        ).fetchall()
        return [dict(f) for f in filas]

    def resumen_libro(self, libro_id):
        fila = self.con.execute(
            """SELECT COUNT(*) AS cantidad,
                      COALESCE(AVG(calificacion), 0) AS promedio
               FROM calificaciones
               WHERE id_libro = ?""",
            (libro_id,)
        ).fetchone()
        return {"cantidad": fila["cantidad"], "promedio": float(fila["promedio"] or 0)}

    def libros_mejor_calificados(self, limite=10):
        filas = self.con.execute(
            """SELECT l.id, l.titulo, l.autor,
                      COUNT(c.id) AS cantidad,
                      COALESCE(AVG(c.calificacion), 0) AS promedio
               FROM libros l
               LEFT JOIN calificaciones c ON c.id_libro = l.id
               GROUP BY l.id
               HAVING COUNT(c.id) > 0
               ORDER BY promedio DESC, cantidad DESC, l.titulo
               LIMIT ?""",
            (limite,)
        ).fetchall()
        return [dict(f) for f in filas]

    def libros_mas_leidos(self, limite=10):
        filas = self.con.execute(
            """SELECT l.id, l.titulo, l.autor,
                      COUNT(p.id) AS prestamos
               FROM libros l
               LEFT JOIN prestamos p ON p.id_libro = l.id
               GROUP BY l.id
               HAVING COUNT(p.id) > 0
               ORDER BY prestamos DESC, l.titulo
               LIMIT ?""",
            (limite,)
        ).fetchall()
        return [dict(f) for f in filas]

    def cerrar(self):
        try:
            self.con.close()
        except sqlite3.Error:
            pass

    def datos_iniciales(self):
        self.con.execute("DELETE FROM prestamos")
        self.con.execute("DELETE FROM solicitudes")
        self.con.execute("DELETE FROM movimientos")
        self.con.execute("DELETE FROM libros")
        self.con.execute("DELETE FROM usuarios")

        for libro in LIBROS_INICIALES:
            self.con.execute(
                "INSERT INTO libros (id, titulo, autor, genero, stock, origen, fecha_alta) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (libro["id"], libro["titulo"], libro["autor"], libro["genero"], libro["stock"], libro["origen"], libro["fecha_alta"])
            )

        for usuario in USUARIOS_INICIALES:
            respuestas = {
                "Neithan Durant": ["firulais", "pizza", "jose"],
                "Jose Carranza": ["max", "hamburguesa", "neithan"],
                "Administrador": ["biblioteca", "libro", "lectura"],
            }[usuario["nombre"]]
            self.con.execute(
                """INSERT INTO usuarios
                (codigo, usuario, nombre, telefono, rol, password, deuda, pagado,
                 pregunta_seguridad, respuesta_seguridad, pregunta_seguridad_2, respuesta_seguridad_2,
                 pregunta_seguridad_3, respuesta_seguridad_3)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    usuario["codigo"], usuario["usuario"], usuario["nombre"], usuario["telefono"], usuario["rol"],
                    hash_password(usuario["password"]), usuario["deuda"], usuario["pagado"],
                    PREGUNTAS_SEGURIDAD[0], hash_password(respuestas[0]),
                    PREGUNTAS_SEGURIDAD[1], hash_password(respuestas[1]),
                    None, None
                )
            )

        self.con.execute(
            "INSERT INTO movimientos (fecha, tipo, detalle) VALUES (?, ?, ?)",
            (hoy_texto(), "SISTEMA", "Sistema iniciado con datos iniciales.")
        )
        self.con.commit()
        self.refrescar_cache()

    def guardar_datos(self):
        """La informacion se guarda inmediatamente con cada INSERT/UPDATE/DELETE.
        Se mantiene este metodo para compatibilidad con la interfaz existente."""
        try:
            self.con.commit()
            self.refrescar_cache()
        except sqlite3.Error:
            self.con.rollback()

    def obtener_multa_por_dia(self):
        """Devuelve la multa configurada por cada día de atraso."""
        fila = self.con.execute(
            "SELECT valor FROM configuracion WHERE clave = 'multa_por_dia' LIMIT 1"
        ).fetchone()

        if fila is None:
            # Valor inicial: L.100 por día.
            self.con.execute(
                "INSERT INTO configuracion (clave, valor) VALUES ('multa_por_dia', '100')"
            )
            self.con.commit()
            return 100.0

        try:
            return float(fila["valor"])
        except (ValueError, TypeError):
            return 100.0

    def cambiar_multa_por_dia(self, nuevo_monto):
        """Guarda la nueva multa y la deja disponible para futuros cálculos."""
        try:
            nuevo_monto = float(nuevo_monto)
        except (ValueError, TypeError):
            return False, "Ingrese un monto numerico."

        if nuevo_monto < 0:
            return False, "La multa no puede ser negativa."

        try:
            self.con.execute(
                """INSERT INTO configuracion (clave, valor)
                   VALUES ('multa_por_dia', ?)
                   ON CONFLICT(clave)
                   DO UPDATE SET valor = excluded.valor""",
                (str(nuevo_monto),)
            )
            self.registrar_movimiento(
                "CONFIGURACION",
                f"Se cambio la multa diaria a L.{nuevo_monto:.2f}."
            )
            self.con.commit()
            self.refrescar_cache()
            return True, f"La multa por dia ahora es de L.{nuevo_monto:.2f}."
        except sqlite3.Error:
            self.con.rollback()
            return False, "No se pudo guardar la nueva multa."

    def registrar_movimiento(self, tipo, detalle):
        self.con.execute(
            "INSERT INTO movimientos (fecha, tipo, detalle) VALUES (?, ?, ?)",
            (hoy_texto(), tipo, detalle)
        )

    # --------------------------------------------------------
    # BUSQUEDAS
    # --------------------------------------------------------

    def preguntas_seguridad_disponibles(self):
        return list(PREGUNTAS_SEGURIDAD)

    def buscar_usuario(self, codigo):
        """Busca por el identificador interno usado por prestamos e historial."""
        fila = self.con.execute(
            "SELECT codigo, usuario, nombre, telefono, rol, password, deuda, pagado, "
            "pregunta_seguridad, respuesta_seguridad, pregunta_seguridad_2, respuesta_seguridad_2, "
            "pregunta_seguridad_3, respuesta_seguridad_3 FROM usuarios WHERE lower(codigo) = lower(?)",
            (codigo,)
        ).fetchone()
        return dict(fila) if fila else None

    def buscar_usuario_login(self, usuario):
        fila = self.con.execute(
            "SELECT codigo, usuario, nombre, telefono, rol, password, deuda, pagado, "
            "pregunta_seguridad, respuesta_seguridad, pregunta_seguridad_2, respuesta_seguridad_2, "
            "pregunta_seguridad_3, respuesta_seguridad_3 FROM usuarios WHERE lower(usuario) = lower(?)",
            (usuario.strip(),)
        ).fetchone()
        return dict(fila) if fila else None

    def autenticar(self, usuario_login, password):
        usuario = self.buscar_usuario_login(usuario_login)
        if usuario is None:
            return None
        if usuario["password"] == hash_password(password):
            return usuario
        # Compatibilidad con bases antiguas que guardaron contraseñas sin hash.
        if usuario["password"] == password:
            nuevo_hash = hash_password(password)
            self.con.execute("UPDATE usuarios SET password = ? WHERE codigo = ?", (nuevo_hash, usuario["codigo"]))
            self.con.commit()
            usuario["password"] = nuevo_hash
            return usuario
        return None

    def generar_codigo_usuario(self, telefono):
        base = telefono[-4:]
        if self.buscar_usuario(base) is None:
            return base
        numero = 1
        while True:
            codigo = f"{base}{numero:02d}"
            if self.buscar_usuario(codigo) is None:
                return codigo
            numero += 1

    def crear_usuario(self, nombre, usuario_login, telefono, password, preguntas, respuestas):
        nombre = nombre.strip()
        usuario_login = usuario_login.strip().lower()
        telefono = telefono.strip()
        password = password.strip()

        if not nombre:
            return None, "El nombre completo es obligatorio."
        if not re.fullmatch(r"@[a-zA-Z0-9_.-]{3,20}", usuario_login):
            return None, "El nombre de usuario debe comenzar con @ y tener entre 3 y 20 caracteres despues del @. Solo se permiten letras, numeros, punto, guion o guion bajo."
        if self.buscar_usuario_login(usuario_login):
            return None, "Ese nombre de usuario ya esta registrado."
        if not telefono.isdigit() or len(telefono) < 4:
            return None, "El telefono debe contener solo numeros y tener al menos 4 digitos."
        if self.con.execute("SELECT 1 FROM usuarios WHERE telefono = ?", (telefono,)).fetchone():
            return None, "Ya existe un usuario con ese telefono."
        if len(password) < 6:
            return None, "La contrasena debe tener al menos 6 caracteres."
        if len(preguntas) != 2 or len(respuestas) != 2:
            return None, "Debe configurar las dos preguntas de seguridad."
        if len(set(preguntas)) != 2:
            return None, "Debe seleccionar dos preguntas de seguridad diferentes."
        if any(not r.strip() for r in respuestas):
            return None, "Debe responder las dos preguntas de seguridad."

        codigo = self.generar_codigo_usuario(telefono)
        try:
            self.con.execute(
                """INSERT INTO usuarios
                (codigo, usuario, nombre, telefono, rol, password, deuda, pagado,
                 pregunta_seguridad, respuesta_seguridad, pregunta_seguridad_2, respuesta_seguridad_2,
                 pregunta_seguridad_3, respuesta_seguridad_3)
                VALUES (?, ?, ?, ?, 'CLIENTE', ?, 0, 0, ?, ?, ?, ?, NULL, NULL)""",
                (codigo, usuario_login, nombre, telefono, hash_password(password),
                 preguntas[0], hash_password(respuestas[0].strip().lower()),
                 preguntas[1], hash_password(respuestas[1].strip().lower()))
            )
            self.registrar_movimiento("USUARIO", f"Se registro el usuario {nombre}.")
            self.con.commit()
            self.refrescar_cache()
            return self.buscar_usuario(codigo), ""
        except sqlite3.IntegrityError:
            self.con.rollback()
            return None, "No se pudo registrar el usuario."

    def actualizar_preguntas_seguridad(self, codigo_usuario, preguntas_respuestas):
        if len(preguntas_respuestas) != 2:
            return False, "Debe configurar las dos preguntas de seguridad."

        preguntas = [p for p, _ in preguntas_respuestas]
        respuestas = [r for _, r in preguntas_respuestas]

        if any(not p or p == "Seleccione una pregunta" for p in preguntas):
            return False, "Debe seleccionar las dos preguntas de seguridad."
        if len(set(preguntas)) != 2:
            return False, "Debe seleccionar dos preguntas de seguridad diferentes."
        if any(not r.strip() for r in respuestas):
            return False, "Debe responder las dos preguntas de seguridad."

        try:
            self.con.execute(
                """UPDATE usuarios
                   SET pregunta_seguridad = ?, respuesta_seguridad = ?,
                       pregunta_seguridad_2 = ?, respuesta_seguridad_2 = ?
                   WHERE codigo = ?""",
                (preguntas[0], hash_password(respuestas[0].strip().lower()),
                 preguntas[1], hash_password(respuestas[1].strip().lower()), codigo_usuario)
            )
            self.registrar_movimiento("SEGURIDAD", f"Se actualizaron las preguntas de seguridad del usuario {codigo_usuario}.")
            self.con.commit()
            self.refrescar_cache()
            return True, "Preguntas de seguridad actualizadas."
        except sqlite3.Error:
            self.con.rollback()
            return False, "No se pudieron actualizar las preguntas de seguridad."

    def cambiar_password(self, usuario, nueva_password):
        nueva_password = nueva_password.strip()
        if len(nueva_password) < 6:
            return False, "La contrasena debe tener al menos 6 caracteres."
        nuevo_hash = hash_password(nueva_password)
        self.con.execute("UPDATE usuarios SET password = ? WHERE codigo = ?", (nuevo_hash, usuario["codigo"]))
        self.registrar_movimiento("SEGURIDAD", f"Se cambio la contrasena de {usuario['nombre']}.")
        self.con.commit()
        self.refrescar_cache()
        return True, "Contrasena actualizada."

    def verificar_preguntas_seguridad(self, usuario_login, respuestas):
        usuario = self.buscar_usuario_login(usuario_login)
        if usuario is None:
            return False, "No se encontro el nombre de usuario."
        if len(respuestas) != 2:
            return False, "Debe responder las dos preguntas de seguridad."

        almacenadas = [
            usuario.get("respuesta_seguridad", ""),
            usuario.get("respuesta_seguridad_2", ""),
        ]
        if any(not x for x in almacenadas):
            return False, "Esta cuenta no tiene configuradas las dos preguntas de seguridad."

        for guardada, respuesta in zip(almacenadas, respuestas):
            if guardada != hash_password(respuesta.strip().lower()):
                return False, "Una o mas respuestas de seguridad no coinciden."
        return True, ""

    def recuperar_password(self, usuario_login, respuestas, nueva_password):
        verificado, mensaje = self.verificar_preguntas_seguridad(usuario_login, respuestas)
        if not verificado:
            return False, mensaje
        usuario = self.buscar_usuario_login(usuario_login)
        return self.establecer_nueva_password(usuario, nueva_password)

    def establecer_nueva_password(self, usuario, nueva_password):
        ok, mensaje = self.cambiar_password(usuario, nueva_password)
        return ok, mensaje

    def registrar_pago(self, codigo_usuario, monto):
        usuario = self.buscar_usuario(codigo_usuario)
        if usuario is None:
            return False, "Usuario no encontrado."

        if monto <= 0:
            return False, "El monto debe ser mayor que 0."

        if monto > usuario["deuda"]:
            return False, "El pago supera la deuda pendiente."

        nueva_deuda = usuario["deuda"] - monto
        nuevo_pagado = usuario["pagado"] + monto
        self.con.execute(
            "UPDATE usuarios SET deuda = ?, pagado = ? WHERE codigo = ?",
            (nueva_deuda, nuevo_pagado, codigo_usuario)
        )
        restante = monto
        multas = self.con.execute(
            "SELECT id, multa FROM prestamos WHERE codigo_usuario = ? AND multa > 0 AND multa_pagada = 0 ORDER BY id",
            (codigo_usuario,)
        ).fetchall()
        for multa_fila in multas:
            valor = float(multa_fila["multa"] or 0)
            if restante + 0.000001 >= valor:
                self.con.execute("UPDATE prestamos SET multa_pagada = 1 WHERE id = ?", (multa_fila["id"],))
                restante -= valor
            else:
                break
        self.registrar_movimiento("PAGO", f"{usuario['nombre']} pago L.{monto:.2f}.")
        self.con.commit()
        self.refrescar_cache()
        return True, "Pago registrado."

    # --------------------------------------------------------
    # LIBROS
    # --------------------------------------------------------

    def agregar_libro(self, titulo, autor, genero, stock, origen):
        genero = genero.strip()
        if genero not in GENEROS_PREDETERMINADOS:
            raise ValueError("Genero no permitido.")
        cursor = self.con.execute(
            "INSERT INTO libros (titulo, autor, genero, stock, origen, fecha_alta) VALUES (?, ?, ?, ?, ?, ?)",
            (titulo, autor, genero, stock, origen, hoy_texto())
        )
        self.registrar_movimiento("LIBRO", f"Se agrego el libro '{titulo}'.")
        self.con.commit()
        self.refrescar_cache()
        return self.buscar_libro(cursor.lastrowid)

    def editar_libro(self, libro_id, titulo, autor, genero, stock, origen):
        genero = genero.strip()
        if genero not in GENEROS_PREDETERMINADOS:
            return False
        libro = self.buscar_libro(libro_id)
        if libro is None:
            return False

        self.con.execute(
            "UPDATE libros SET titulo = ?, autor = ?, genero = ?, stock = ?, origen = ? WHERE id = ?",
            (titulo, autor, genero, stock, origen, libro_id)
        )
        self.registrar_movimiento("LIBRO", f"Se modifico el libro '{titulo}'.")
        self.con.commit()
        self.refrescar_cache()
        return True

    def eliminar_libro(self, libro_id):
        libro = self.buscar_libro(libro_id)
        if libro is None:
            return False, "Libro no encontrado."

        activo = self.con.execute(
            "SELECT 1 FROM prestamos WHERE id_libro = ? AND estado = 'PRESTADO' LIMIT 1",
            (libro_id,)
        ).fetchone()
        if activo:
            return False, "No puede eliminar un libro con un prestamo activo."

        historico = self.con.execute("SELECT 1 FROM prestamos WHERE id_libro = ? LIMIT 1", (libro_id,)).fetchone()
        if historico:
            return False, "No puede eliminar un libro que tiene historial de prestamos."

        self.con.execute("DELETE FROM libros WHERE id = ?", (libro_id,))
        self.registrar_movimiento("LIBRO", f"Se elimino el libro '{libro['titulo']}'.")
        self.con.commit()
        self.refrescar_cache()
        return True, "Libro eliminado."

    def buscar_libro(self, libro_id):
        fila = self.con.execute(
            "SELECT id, titulo, autor, genero, stock, origen, fecha_alta FROM libros WHERE id = ? LIMIT 1",
            (libro_id,)
        ).fetchone()
        return dict(fila) if fila else None

    def buscar_libros(self, texto="", autor="", genero=""):
        sql = """
            SELECT id, titulo, autor, genero, stock, origen, fecha_alta
            FROM libros
            WHERE 1 = 1
        """
        parametros = []

        texto = texto.strip()
        autor = autor.strip()
        genero = genero.strip()

        if texto:
            sql += " AND (lower(titulo) LIKE ? OR lower(autor) LIKE ?)"
            patron = f"%{texto.lower()}%"
            parametros.extend([patron, patron])

        if autor:
            sql += " AND lower(autor) LIKE ?"
            parametros.append(f"%{autor.lower()}%")

        if genero:
            sql += " AND lower(genero) = ?"
            parametros.append(genero.lower())

        sql += " ORDER BY id"
        return [dict(f) for f in self.con.execute(sql, parametros)]

    # --------------------------------------------------------
    # PRESTAMOS
    # --------------------------------------------------------

    def prestamos_usuario(self, codigo):
        return [dict(f) for f in self.con.execute(
            "SELECT id, codigo_usuario, id_libro, fecha_prestamo, fecha_vencimiento, fecha_devolucion, estado, multa, multa_pagada FROM prestamos WHERE codigo_usuario = ? ORDER BY id",
            (codigo,)
        )]

    def activos_usuario(self, codigo):
        return [dict(f) for f in self.con.execute(
            "SELECT id, codigo_usuario, id_libro, fecha_prestamo, fecha_vencimiento, fecha_devolucion, estado, multa, multa_pagada FROM prestamos WHERE codigo_usuario = ? AND estado = 'PRESTADO' ORDER BY id",
            (codigo,)
        )]

    def crear_prestamo(self, codigo_usuario, libro_id):
        self.actualizar_multas_vencidas()
        usuario = self.buscar_usuario(codigo_usuario)
        libro = self.buscar_libro(libro_id)

        if usuario is None:
            return False, "Usuario no encontrado."
        if libro is None:
            return False, "El libro no existe."

        if usuario["rol"] == "CLIENTE" and usuario["deuda"] > 0.000001:
            return False, (
                f"Tienes una deuda pendiente de L.{usuario['deuda']:.2f}. "
                "Debes realizar el pago en la ventanilla de la biblioteca "
                "antes de solicitar otro libro."
            )

        if usuario["rol"] == "CLIENTE":
            vencidos = [p for p in self.activos_usuario(codigo_usuario) if self.estado_prestamo(p) == "VENCIDO"]
            if vencidos:
                return False, (
                    "Tienes un prestamo vencido. Debes devolver el libro y pagar la multa correspondiente "
                    "en la ventanilla de la biblioteca antes de solicitar otro libro."
                )

        activos = self.activos_usuario(codigo_usuario)
        if len(activos) >= MAX_LIBROS:
            return False, "El usuario ya tiene el maximo de prestamos."

        repetido = self.con.execute(
            "SELECT 1 FROM prestamos WHERE codigo_usuario = ? AND id_libro = ? AND estado = 'PRESTADO'",
            (codigo_usuario, libro_id)
        ).fetchone()
        if repetido:
            return False, "El usuario ya tiene este libro prestado."

        libro_actual = self.buscar_libro(libro_id)
        if libro_actual is None or libro_actual["stock"] <= 0:
            return False, "NO DISPONIBLE"

        fecha_prestamo = date.today()
        fecha_vencimiento = fecha_prestamo + timedelta(days=DIAS_PRESTAMO)

        try:
            self.con.execute("UPDATE libros SET stock = stock - 1 WHERE id = ? AND stock > 0", (libro_id,))
            if self.con.execute("SELECT changes() AS c").fetchone()["c"] != 1:
                self.con.rollback()
                return False, "NO DISPONIBLE"

            cursor = self.con.execute(
                """INSERT INTO prestamos
                (codigo_usuario, id_libro, fecha_prestamo, fecha_vencimiento, fecha_devolucion, estado, multa, multa_pagada)
                VALUES (?, ?, ?, ?, ?, 'PRESTADO', 0, 1)""",
                (codigo_usuario, libro_id, fecha_prestamo.isoformat(), fecha_vencimiento.isoformat(), "")
            )
            self.registrar_movimiento("PRESTAMO", f"{usuario['nombre']} saco '{libro['titulo']}'.")
            self.con.commit()
            self.refrescar_cache()
            return True, fecha_vencimiento
        except sqlite3.Error:
            self.con.rollback()
            return False, "No se pudo registrar el prestamo."

    def devolver_prestamo_por_id(self, prestamo_id):
        fila = self.con.execute(
            """SELECT id, codigo_usuario, id_libro, fecha_prestamo,
                      fecha_vencimiento, fecha_devolucion, estado, multa, multa_pagada
               FROM prestamos
               WHERE id = ? AND estado = 'PRESTADO'
               LIMIT 1""",
            (prestamo_id,)
        ).fetchone()

        if not fila:
            return False, 0

        prestamo = dict(fila)
        hoy = date.today()
        vencimiento = date.fromisoformat(prestamo["fecha_vencimiento"])
        dias_atraso = max((hoy - vencimiento).days, 0)
        multa = dias_atraso * self.obtener_multa_por_dia()
        multa_anterior = float(prestamo.get("multa", 0) or 0)
        incremento_deuda = max(multa - multa_anterior, 0)

        libro = self.buscar_libro(prestamo["id_libro"])
        usuario = self.buscar_usuario(prestamo["codigo_usuario"])

        try:
            if libro:
                self.con.execute(
                    "UPDATE libros SET stock = stock + 1 WHERE id = ?",
                    (prestamo["id_libro"],)
                )

            self.con.execute(
                """UPDATE prestamos
                   SET estado='DEVUELTO',
                       fecha_devolucion=?,
                       multa=?,
                       multa_pagada=?
                   WHERE id=?""",
                (
                    hoy.isoformat(),
                    multa,
                    1 if multa == 0 else 0,
                    prestamo_id
                )
            )

            if usuario and incremento_deuda > 0:
                self.con.execute(
                    "UPDATE usuarios SET deuda = deuda + ? WHERE codigo = ?",
                    (incremento_deuda, prestamo["codigo_usuario"])
                )

            titulo = libro["titulo"] if libro else "Desconocido"
            nombre = usuario["nombre"] if usuario else prestamo["codigo_usuario"]

            self.registrar_movimiento(
                "DEVOLUCION",
                f"{nombre} devolvio '{titulo}'."
            )

            self.con.commit()
            self.refrescar_cache()
            return True, multa

        except sqlite3.Error:
            self.con.rollback()
            return False, 0

    def devolver_libro(self, codigo_usuario, libro_id):
        prestamo = self.con.execute(
            """SELECT id, codigo_usuario, id_libro, fecha_prestamo, fecha_vencimiento,
                      fecha_devolucion, estado, multa, multa_pagada
               FROM prestamos
               WHERE codigo_usuario = ? AND id_libro = ? AND estado = 'PRESTADO'
               LIMIT 1""",
            (codigo_usuario, libro_id)
        ).fetchone()

        if not prestamo:
            return False, 0

        prestamo = dict(prestamo)
        hoy = date.today()
        vencimiento = date.fromisoformat(prestamo["fecha_vencimiento"])
        dias_atraso = max((hoy - vencimiento).days, 0)
        multa = dias_atraso * self.obtener_multa_por_dia()
        multa_anterior = float(prestamo.get("multa", 0) or 0)
        incremento_deuda = max(multa - multa_anterior, 0)

        libro = self.buscar_libro(libro_id)
        usuario = self.buscar_usuario(codigo_usuario)

        try:
            if libro:
                self.con.execute("UPDATE libros SET stock = stock + 1 WHERE id = ?", (libro_id,))

            self.con.execute(
                "UPDATE prestamos SET estado = 'DEVUELTO', fecha_devolucion = ?, multa = ?, multa_pagada = ? WHERE id = ?",
                (hoy.isoformat(), multa, 1 if multa == 0 else 0, prestamo["id"])
            )

            if usuario and incremento_deuda > 0:
                self.con.execute("UPDATE usuarios SET deuda = deuda + ? WHERE codigo = ?", (incremento_deuda, codigo_usuario))

            titulo = libro["titulo"] if libro else "Desconocido"
            nombre = usuario["nombre"] if usuario else codigo_usuario
            self.registrar_movimiento("DEVOLUCION", f"{nombre} devolvio '{titulo}'.")
            self.con.commit()
            self.refrescar_cache()
            return True, multa
        except sqlite3.Error:
            self.con.rollback()
            return False, 0

    def estado_prestamo(self, prestamo):
        if prestamo["estado"] == "DEVUELTO":
            return "DEVUELTO"

        vencimiento = date.fromisoformat(prestamo["fecha_vencimiento"])
        diferencia = (vencimiento - date.today()).days

        if diferencia < 0:
            return "VENCIDO"
        if diferencia == 0:
            return "VENCE HOY"
        if diferencia == 1:
            return "FALTA 1 DIA"
        if diferencia == 2:
            return "FALTAN 2 DIAS"

        return "VIGENTE"

    # --------------------------------------------------------
    # SOLICITUDES
    # --------------------------------------------------------

    def crear_solicitud(self, codigo_usuario, tipo, titulo, autor="", genero="", comentario="", id_libro=None):
        if genero and genero not in GENEROS_PREDETERMINADOS:
            return None
        cursor = self.con.execute(
            """INSERT INTO solicitudes
               (codigo_usuario, id_libro, tipo, titulo, autor, genero, comentario, estado, fecha)
               VALUES (?, ?, ?, ?, ?, ?, ?, 'PENDIENTE', ?)""",
            (codigo_usuario, id_libro, tipo, titulo, autor, genero, comentario, hoy_texto())
        )
        self.registrar_movimiento("SOLICITUD", f"Nueva solicitud de tipo {tipo}: '{titulo}'.")
        self.con.commit()
        self.refrescar_cache()
        fila = self.con.execute(
            "SELECT id, codigo_usuario, id_libro, tipo, titulo, autor, genero, comentario, estado, fecha FROM solicitudes WHERE id = ?",
            (cursor.lastrowid,)
        ).fetchone()
        return dict(fila)

    def cambiar_estado_solicitud(self, solicitud_id, estado):
        fila = self.con.execute("SELECT 1 FROM solicitudes WHERE id = ?", (solicitud_id,)).fetchone()
        if not fila:
            return False

        self.con.execute("UPDATE solicitudes SET estado = ? WHERE id = ?", (estado, solicitud_id))
        self.registrar_movimiento("SOLICITUD", f"Solicitud #{solicitud_id}: {estado}.")
        self.con.commit()
        self.refrescar_cache()
        return True



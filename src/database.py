from psycopg2.pool import ThreadedConnectionPool
import logging
import main as mainfile


_pool = None
logger = logging.getLogger(__name__)

def init_pool():
    global _pool
    _pool = ThreadedConnectionPool(
        1, 10,
        host=mainfile.LOCALHOST,
        database=mainfile.DATABASE,
        user=mainfile.USER,
        # password=PASSWORD
    )

def get_conn():
    return _pool.getconn()

def put_conn(conn):
    _pool.putconn(conn)

def close_all():
    _pool.closeall()


# FUNCIONES SESION
def update_sesion_estado(conn, sesion_id, estado):
    with conn.cursor() as cur:
        query = """
        UPDATE sesion
        SET estado = %s, finaliza = now()::time(0)
        WHERE sesion_id = %s
        """
        cur.execute(query, (estado, sesion_id))
    conn.commit()
    logger.info(f"[DATABASE] Sesión con ID [{sesion_id}] {estado}.")

def insert_nueva_sesion(conn, horario_id, fecha):
    with conn.cursor() as cur:
        query = """
        INSERT INTO sesion
        (horario_id, fecha, comienza, estado)
        VALUES (%s, %s, NOW()::time(0), %s)
        RETURNING sesion_id
        """
        cur.execute(query, (
            horario_id,
            fecha,
            "en_curso"
        ))
        sesion_id = cur.fetchone()[0]
    conn.commit()
    logger.info(f"[DATABASE] Sesión con ID [{sesion_id}] creada y en curso.")
    return sesion_id

def find_sesion(conn, horario_id, fecha):
    with conn.cursor() as cur:
        query = """
        SELECT sesion_id
        FROM sesion
        WHERE horario_id = %s
        AND fecha = %s
        """
        cur.execute(query, (horario_id, fecha))
        return cur.fetchone()

def find_estado_sesion(conn, sesion_id):
    with conn.cursor() as cur:
        query = """
        SELECT estado
        FROM sesion
        WHERE sesion_id = %s
        """
        cur.execute(query, (sesion_id,))
        res = cur.fetchone()
        return res[0] if res else None
    
def get_sesiones_por_fecha(conn, fecha):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                s.sesion_id,
                h.profesor,
                h.grupo,
                h.asignatura,
                h.aula,
                s.comienza,
                s.finaliza
            FROM sesion s
            JOIN horario h
                ON s.horario_id = h.horario_id
            WHERE s.fecha = %s
            ORDER BY s.comienza
        """, (fecha,))

        return cur.fetchall()
    
def get_estadisticas_sensores_por_sesion(conn, sesion_id):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                sensor_id,
                MAX(valor),
                MIN(valor),
                AVG(valor)
            FROM lectura
            WHERE sesion_id = %s
            GROUP BY sensor_id
        """, (sesion_id,))

        return cur.fetchall()
    
def get_alarmas_por_codigo_por_sesion(conn, sesion_id):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                codigo,
                sensor_id,
                COUNT(*) as total
            FROM alerta
            WHERE sesion_id = %s
            GROUP BY codigo, sensor_id
            ORDER BY total DESC
        """, (sesion_id,))

        return cur.fetchall()

def get_sesiones_por_semana(conn, fecha_inicio, fecha_fin):

    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                s.sesion_id,
                h.profesor,
                h.grupo,
                h.asignatura,
                h.aula,
                s.fecha,
                s.comienza,
                s.finaliza
            FROM sesion s
            JOIN horario h ON s.horario_id = h.horario_id
            WHERE s.fecha BETWEEN %s AND %s
            ORDER BY s.fecha, s.comienza
        """, (fecha_inicio, fecha_fin))

        return cur.fetchall()

def get_profesores_por_semana(conn, fecha_inicio, fecha_fin):

    with conn.cursor() as cur:
        cur.execute("""
            SELECT DISTINCT h.profesor
            FROM sesion s
            JOIN horario h ON s.horario_id = h.horario_id
            WHERE s.fecha BETWEEN %s AND %s
            ORDER BY h.profesor
        """, (fecha_inicio, fecha_fin))

        return [row[0] for row in cur.fetchall()]



# FUNCIONES HORARIO
def find_horario(conn, aula, dia_semana, hora_actual):
    with conn.cursor() as cur:
        query = """
        SELECT horario_id
        FROM horario
        WHERE aula = %s
        AND dia_semana = %s
        AND %s BETWEEN hora_inicio AND hora_fin
        """
        cur.execute(query, (aula, dia_semana, hora_actual))
        return cur.fetchone()
    

# FUNCIONES SENSOR
def find_sensor_tipo(conn, sensor_id):
    with conn.cursor() as cur:
        query = """
        SELECT tipo
        FROM sensor
        WHERE sensor_id = %s
        """
        cur.execute(query, (sensor_id,))
        result = cur.fetchone()
        return result[0] if result else None

def find_validez_sensor(conn, sensor_id):
    with conn.cursor() as cur:
        query = """
        SELECT validez
        FROM sensor
        WHERE sensor_id = %s
        """
        cur.execute(query, (sensor_id,))
        res = cur.fetchone()
        return res[0] if res else None

def find_todos_los_sensores(conn):
    with conn.cursor() as cur:
        query = """
        SELECT sensor_id, tipo, validez, estado
        FROM sensor
        """
        cur.execute(query)
        return cur.fetchall()

def find_todos_los_sensores_tipo(conn, tipo):
    with conn.cursor() as cur:
        query = """
        SELECT sensor_id, tipo, validez, estado
        FROM sensor
        WHERE tipo IN (%s, 'mixto')
        """
        cur.execute(query, (tipo,))
        return cur.fetchall()

def update_estado_sensor(conn, sensor_id, estado):
    with conn.cursor() as cur:
        query = """
        UPDATE sensor
        SET estado = %s
        WHERE sensor_id = %s
        """
        cur.execute(query, (estado,sensor_id))
    conn.commit()
    logger.info(f"[DATABASE] Sensor '{sensor_id}' {estado}.")
    

# FUNCIONES LECTURA
def insert_lectura(conn, sensor_id, valor, timestamp, sesion_id):
    with conn.cursor() as cur:
        query = """
        INSERT INTO lectura
        (sensor_id, valor, timestamp, sesion_id)
        VALUES (%s, %s, %s, %s)
        """
        cur.execute(query, (sensor_id, valor, timestamp, sesion_id))
    conn.commit()
    logger.info(f"[DATABASE] Nueva lectura: Sensor {sensor_id}: [{valor}] -  [{timestamp}]")

def find_ultima_lectura_por_sensor(conn, sesion_id):
    with conn.cursor() as cur:
        query = """
        SELECT l.sensor_id, l.valor, l.timestamp
        FROM lectura l
        JOIN (
            SELECT sensor_id, MAX(timestamp) AS max_timestamp
            FROM lectura
            WHERE sesion_id = %s
            GROUP BY sensor_id
        ) AS max_lecturas ON l.sensor_id = max_lecturas.sensor_id AND l.timestamp = max_lecturas.max_timestamp
        """
        cur.execute(query, (sesion_id,))
        return cur.fetchall()


# FUNCIONES EVALUACION
def insert_evaluacion(conn, sesion_id, puntuacion):
    with conn.cursor() as cur:
        query = """
        INSERT INTO evaluacion
        (sesion_id, puntuacion, timestamp)
        VALUES (%s, %s, NOW()::timestamp(0))
        """
        cur.execute(query, (sesion_id, puntuacion))
    conn.commit()
    logger.info(f"[DATABASE] Nueva evaluación: Sesión {sesion_id}: [{puntuacion}]")


# FUNCIONES ALERTAS
def insert_alerta(conn, sensor_id, texto, codigo, nivel, sesion_id):
    with conn.cursor() as cur:
        query = """
        INSERT INTO alerta
        (sensor_id, texto, codigo, nivel, timestamp, sesion_id, reconocida)
        VALUES (%s, %s, %s, %s, NOW()::timestamp(0), %s, FALSE)
        RETURNING alerta_id
        """
        cur.execute(query, (sensor_id, texto, codigo, nivel, sesion_id))
        alerta_id = cur.fetchone()[0]
    conn.commit()
    logger.info(f"[DATABASE] Nueva alerta: Sesión {sesion_id}: [{nivel}] {sensor_id}({codigo}) - {texto}")
    return alerta_id

def find_reconocimiento_alerta_por_codigo_en_sesion(conn, codigo, sesion_id):
    with conn.cursor() as cur:
        query = """
        SELECT alerta_id, reconocida
        FROM alerta
        WHERE sesion_id = %s AND codigo = %s
        ORDER BY timestamp DESC
        LIMIT 1
        """
        cur.execute(query, (sesion_id, codigo))
        return cur.fetchone()

def update_reconocimiento_alerta(conn, alerta_id, reconocida):
    with conn.cursor() as cur:
        query = """
        UPDATE alerta
        SET reconocida = %s
        WHERE alerta_id = %s
        """
        cur.execute(query, (reconocida,alerta_id))
    conn.commit()
    logger.info(f"[DATABASE] Alerta '{alerta_id}' recnonocida: {reconocida}")

# FUNCION INFORME
def get_metricas_profesor_semanal(conn, profesor, fecha_inicio, fecha_fin):

    with conn.cursor() as cur:

        # SONIDO
        cur.execute("""
            SELECT
                MAX(l.valor),
                MIN(l.valor),
                AVG(l.valor)
            FROM lectura l
            JOIN sesion s ON l.sesion_id = s.sesion_id
            JOIN horario h ON s.horario_id = h.horario_id
            WHERE h.profesor = %s
              AND l.sensor_id = 'son'
              AND s.fecha BETWEEN %s AND %s
        """, (profesor, fecha_inicio, fecha_fin))

        sonido = cur.fetchone()

        # ALARMAS
        cur.execute("""
            SELECT
                a.codigo,
                COUNT(*)
            FROM alerta a
            JOIN sesion s ON a.sesion_id = s.sesion_id
            JOIN horario h ON s.horario_id = h.horario_id
            WHERE h.profesor = %s
              AND s.fecha BETWEEN %s AND %s
            GROUP BY a.codigo
        """, (profesor, fecha_inicio, fecha_fin))

        alarmas = cur.fetchall()

        # DURACION
        cur.execute("""
            SELECT
                AVG(EXTRACT(EPOCH FROM (s.finaliza - s.comienza)))
            FROM sesion s
            JOIN horario h ON s.horario_id = h.horario_id
            WHERE h.profesor = %s
              AND s.fecha BETWEEN %s AND %s
        """, (profesor, fecha_inicio, fecha_fin))

        duracion = cur.fetchone()[0]

    return {
        "sonido": sonido,
        "alarmas": alarmas,
        "duracion_media": duracion
    }

def get_aulas_semana(conn, fecha_inicio, fecha_fin):

    with conn.cursor() as cur:
        cur.execute("""
            SELECT DISTINCT h.aula
            FROM sesion s
            JOIN horario h ON s.horario_id = h.horario_id
            WHERE s.fecha BETWEEN %s AND %s
            ORDER BY h.aula
        """, (fecha_inicio, fecha_fin))

        return [row[0] for row in cur.fetchall()]
    
def get_grupos_semana(conn, fecha_inicio, fecha_fin):

    with conn.cursor() as cur:
        cur.execute("""
            SELECT DISTINCT h.grupo
            FROM sesion s
            JOIN horario h ON s.horario_id = h.horario_id
            WHERE s.fecha BETWEEN %s AND %s
            ORDER BY h.grupo
        """, (fecha_inicio, fecha_fin))

        return [row[0] for row in cur.fetchall()]

def get_sonido_semana_por_aula(conn, aula, fecha_inicio, fecha_fin):

    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                MAX(l.valor),
                MIN(l.valor),
                AVG(l.valor)
            FROM lectura l
            JOIN sesion s ON l.sesion_id = s.sesion_id
            JOIN horario h ON s.horario_id = h.horario_id
            WHERE h.aula = %s
              AND l.sensor_id = 'son'
              AND s.fecha BETWEEN %s AND %s
        """, (aula, fecha_inicio, fecha_fin))

        res = cur.fetchone()
        return res if res else None

def get_sonido_semana_por_grupo(conn, grupo, fecha_inicio, fecha_fin):

    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                MAX(l.valor),
                MIN(l.valor),
                AVG(l.valor)
            FROM lectura l
            JOIN sesion s ON l.sesion_id = s.sesion_id
            JOIN horario h ON s.horario_id = h.horario_id
            WHERE h.grupo = %s
              AND l.sensor_id = 'son'
              AND s.fecha BETWEEN %s AND %s
        """, (grupo, fecha_inicio, fecha_fin))

        res = cur.fetchone()
        return res if res else None
    

    
def get_estadisticas_sensores_por_sesion(conn, sesion_id):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                sensor_id,
                MAX(valor),
                MIN(valor),
                AVG(valor)
            FROM lectura
            WHERE sesion_id = %s
            GROUP BY sensor_id
        """, (sesion_id,))

        return cur.fetchall()

def get_metricas_aula_semanal(conn, aula, fecha_inicio, fecha_fin):

    with conn.cursor() as cur:

        cur.execute("""
            SELECT
                l.sensor_id,
                MAX(l.valor),
                MIN(l.valor),
                AVG(l.valor)
            FROM lectura l
            JOIN sesion s ON l.sesion_id = s.sesion_id
            JOIN horario h ON s.horario_id = h.horario_id
            WHERE h.aula = %s
              AND l.sensor_id IN ('tem', 'hum', 'son', 'luz')
              AND s.fecha BETWEEN %s AND %s
            GROUP BY l.sensor_id
            ORDER BY l.sensor_id;
        """, (aula, fecha_inicio, fecha_fin))

        ambientales = cur.fetchall()

        cur.execute("""
            SELECT
                a.codigo,
                COUNT(*)
            FROM alerta a
            JOIN sesion s ON a.sesion_id = s.sesion_id
            JOIN horario h ON s.horario_id = h.horario_id
            WHERE h.aula = %s
              AND s.fecha BETWEEN %s AND %s
            GROUP BY a.codigo
            ORDER BY a.codigo;
        """, (aula, fecha_inicio, fecha_fin))

        alarmas = cur.fetchall()

    return {
        "ambientales": ambientales,
        "alarmas": alarmas
    }


# FUNCIONES DB
def main_delete_db(conn):
    files = ["/TFG-fravilde1/src/postgres/drop.sql", "/TFG-fravilde1/src/postgres/schema.sql", "/TFG-fravilde1/src/postgres/seed.sql"]
    with conn.cursor() as cur:
        for f in files:
            cur.execute(open(mainfile.PROJECT_PATH + f, encoding="utf-8").read())
    conn.commit()

def main_check_db(table_name, conn):
    with conn.cursor() as cur:
        cur.execute(f"SELECT * FROM {table_name}")
        rows = cur.fetchall()
        for row in rows:
            print(row)

if __name__ == "__main__":
    init_pool()
    conn = get_conn()

    main_delete_db(conn)
    # main_check_db("sensor", conn)
    # main_check_db("sesion", conn)
    # insert_alerta(conn, 'tem', 'EX', 'AVtemX', 'AVISO', 1)
    # main_check_db("alerta", conn)
    # alarm.lanzar_popup_alerta('HOLA',25,conn)
    # main_check_db("evaluacion", conn)
    # print(insert_alerta(conn, 'tem', 'EX', 'AVT1', 'AVISO', 1))
    # print(find_reconocimiento_alerta_por_codigo_en_sesion(conn, 'AVT1', 1)[0])

    # ================= TESTING FUNCTIONS ================

    # ack_alerta = find_reconocimiento_alerta_por_codigo_en_sesion(conn, 'AVT1', 1)
    # print(ack_alerta)
    # if ack_alerta == None or not ack_alerta[1]:
    #     print("O no existe todavia o no está ack, creamos otra")
    # elif ack_alerta:
    #     print("existia una y está ack, no hacemos nada")

    # update_reconocimiento_alerta(conn, ack_alerta[0], True)
    # ack_alerta = find_reconocimiento_alerta_por_codigo_en_sesion(conn, 'AVT1', 1)
    # print(ack_alerta)
    # if ack_alerta == None or not ack_alerta[1]:
    #     print("O no existe todavia o no está ack, creamos otra")
    # elif ack_alerta:
    #     print("existia una y está ack, no hacemos nada")



    # =====================================================

    put_conn(conn)
    close_all()
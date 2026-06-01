import psycopg2

PROJECT_PATH = "I:/UNIVERSIDAD/TFG"

def update_sesion_estado(conn, sesion_id, estado):
    with conn.cursor() as cur:
        query = """
        UPDATE sesion
        SET estado = %s, finaliza = now()::time(0)
        WHERE sesion_id = %s
        """
        cur.execute(query, (estado, sesion_id))
    conn.commit()
    print(f"[DATABASE] Sesión con ID [{sesion_id}] {estado}.")

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
    print(f"[DATABASE] Sesión con ID [{sesion_id}] creada y en curso.")
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

def insert_lectura(conn, sensor_id, valor, timestamp, sesion_id):
    with conn.cursor() as cur:
        query = """
        INSERT INTO lectura
        (sensor_id, valor, timestamp, sesion_id)
        VALUES (%s, %s, %s, %s)
        """
        cur.execute(query, (sensor_id, valor, timestamp, sesion_id))
    conn.commit()
    print(f"[DATABASE] Nueva lectura: Sensor {sensor_id}: [{valor}] -  [{timestamp}]")

def main_delete_db(conn):
    files = ["/TFG-fravilde1/src/postgres/drop.sql", "/TFG-fravilde1/src/postgres/schema.sql", "/TFG-fravilde1/src/postgres/seed.sql"]
    with conn.cursor() as cur:
        for f in files:
            cur.execute(open(PROJECT_PATH + f, encoding="utf-8").read())
    conn.commit()

def main_check_db(table_name, conn):
    with conn.cursor() as cur:
        cur.execute(f"SELECT * FROM {table_name}")
        rows = cur.fetchall()
        for row in rows:
            print(row)

if __name__ == "__main__":
    conn = psycopg2.connect(
        host="localhost",
        database="fravilde1_tfg",
        user="postgres",
        # password="admin"
    )
    main_delete_db(conn)
    # main_check_db("lectura", conn)
    conn.close()
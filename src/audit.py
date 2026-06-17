import logging
import database
from datetime import datetime
from datetime import timedelta


logger = logging.getLogger(__name__)


def get_informe_diario(conn, fecha):

    sesiones = database.get_sesiones_por_fecha(conn, fecha)

    print("\n")
    print("=" * 60)
    print(f"\nInforme Diario  ({fecha})")

    for sesion in sesiones:

        sesion_id, profesor, grupo, asignatura, aula, comienza, finaliza = sesion
        fecha = datetime.strptime(str(fecha), "%Y-%m-%d").date()

        inicio = datetime.combine(fecha, comienza)
        fin = datetime.combine(fecha, finaliza)

        duracion = fin - inicio

        print(f"\nSESIÓN {sesion_id}")
        print(f"  Profesor:   {profesor}")
        print(f"  Aula:       {aula}")
        print(f"  Grupo:      {grupo}")
        print(f"  Asignatura: {asignatura}")
        print(f"  Duración:   {duracion}")
        
        stats_sensores = database.get_estadisticas_sensores_por_sesion(conn,sesion_id)

        print("\nSENSORES:")
        for s in stats_sensores:
            sensor, maxv, minv, avg = s
            maxv = maxv if maxv is not None else 0
            minv = minv if minv is not None else 0
            avg  = avg  if avg  is not None else 0
            print(f"{sensor}:")
            print(f"  Max: {maxv:.2f}")
            print(f"  Min: {minv:.2f}")
            print(f"  Media: {avg:.2f}\n")

        stats_alarmas = database.get_alarmas_por_codigo_por_sesion(conn,sesion_id)
        
        print("ALARMAS:")
        for a in stats_alarmas:
            codigo, sensor, total = a
            print(f"{codigo}: {total}")


        print("\n")
        print("=" * 60)

def get_informe_semanal(conn, fecha):

    fecha_fin = datetime.strptime(str(fecha), "%Y-%m-%d").date()
    fecha_inicio = fecha_fin - timedelta(days=fecha_fin.weekday())

    fechas = [
        fecha_inicio + timedelta(days=i)
        for i in range((fecha_fin - fecha_inicio).days + 1)
    ]

    print("\n")
    print("=" * 60)
    print(f"\nINFORME SEMANAL ({fecha_inicio} - {fecha_fin})")
    print("=" * 60)

    for fecha in fechas:
        get_informe_diario(conn, fecha.strftime("%Y-%m-%d"))

    print("=" * 60)
    print(f"\n INFORME PROFESORADO ({fecha_inicio} - {fecha_fin})")
    
    profesores = database.get_profesores_por_semana(conn, fecha_inicio, fecha_fin)

    for prof in profesores:

        datos = database.get_metricas_profesor_semanal(conn, prof, fecha_inicio, fecha_fin)

        print("\n" + "=" * 60)
        print(f"PROFESOR: {prof}")
        print("=" * 60)

        maxv, minv, avg = datos["sonido"]
        maxv = maxv if maxv is not None else 0
        minv = minv if minv is not None else 0
        avg  = avg  if avg  is not None else 0

        print("\nSONIDO:")
        print(f"  Max: {maxv:.2f}")
        print(f"  Min: {minv:.2f}")
        print(f"  Media: {avg:.2f}\n")

        print("\nALARMAS:")
        for nivel, total in datos["alarmas"]:
            print(f"  {nivel}: {total}")

        if datos["duracion_media"]:
            horas = datos["duracion_media"] // 3600
            print("\nDURACIÓN MEDIA:")
            print(f"  {horas:.2f}h")
    

    print("=" * 60)
    print(f"\n INFORME AULAS ({fecha_inicio} - {fecha_fin})")

    aulas = database.get_aulas_semana(conn, fecha_inicio, fecha_fin)

    for aula in aulas:

        print("\n" + "=" * 60)
        print(f"AULA: {aula}")
        print("=" * 60)

        datos = database.get_metricas_aula_semanal(conn, aula, fecha_inicio, fecha_fin)

        print("\nSENSORES")
        for sensor, maxv, minv, avg in datos["ambientales"]:
            maxv = maxv if maxv is not None else 0
            minv = minv if minv is not None else 0
            avg = avg if avg is not None else 0

            print(f"\n{sensor}")
            print(f"  Max: {maxv:.2f}")
            print(f"  Min: {minv:.2f}")
            print(f"  Media: {avg:.2f}")

        # -------------------------
        # ALARMAS
        # -------------------------
        print("\nALARMAS")

        for nivel, total in datos["alarmas"]:
            print(f"  {nivel}: {total}")

    print("=" * 60)
    print(f"\n INFORME GRUPOS ({fecha_inicio} - {fecha_fin})")

    grupos = database.get_grupos_semana(conn, fecha_inicio, fecha_fin)

    for grupo in grupos:

        datos = database.get_sonido_semana_por_grupo(conn, grupo, fecha_inicio, fecha_fin)

        print("\n" + "=" * 60)
        print(f"GRUPO: {grupo}")
        print("=" * 60)

        maxv, minv, avg = datos
        maxv = maxv if maxv is not None else 0
        minv = minv if minv is not None else 0
        avg  = avg  if avg  is not None else 0

        print("\nSONIDO:")
        print(f"  Max: {maxv:.2f}")
        print(f"  Min: {minv:.2f}")
        print(f"  Media: {avg:.2f}\n")


def formulario_borrar_base_datos(conn):
    while True:
        sino = input("\n¿DESEA BORRAR LA BASE DE DATOS? (S/N):").strip()
        if sino == "S":
            database.main_delete_db(conn)
        if sino =="N":
            break
        else:
            logger.warning("[AUDIT] No existe acción para la instrucción introducida.")

def formulario_informe(conn, fecha):
    while True:
        print("\nSi desea un informe diario introduzca 'DIARIO'.")
        print("Si desea un informe diario introduzca 'SEMANAL'. NOTA: Si elige el informe semanal luego se le preguntará si desea borrar la base de datos.")
        informe = input("\n\t · Introduzca el informe deseado:").strip()

        if informe != "DIARIO" and informe!= "SEMANAL":
                logger.warning("[AUDIT] No existe acción para la instrucción introducida.")
        
        elif informe == "DIARIO":
            get_informe_diario(conn, fecha)
        
        elif informe == "SEMANAL":
            get_informe_semanal(conn, fecha)
            formulario_borrar_base_datos(conn)
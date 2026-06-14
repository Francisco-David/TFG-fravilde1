import database
import logging
import subprocess
import sys

DEMO_PROJECT_PATH = "I:/UNIVERSIDAD/TFG/TFG-fravilde1"

UMBRAL_AVISO_TEM_MAX = 28
UMBRAL_ALARMA_TEM_MAX = 35
UMBRAL_AVISO_TEM_MIN = 10
UMBRAL_ALARMA_TEM_MIN = 5

UMBRAL_AVISO_SON_MAX = 150
UMBRAL_ALARMA_SON_MAX = 180

UMBRAL_AVISO_HUM_MAX = 70
UMBRAL_ALARMA_HUM_MAX = 85

UMBRAL_AVISO_LUZ_MIN = 20
UMBRAL_ALARMA_LUZ_MIN = 10


logger = logging.getLogger(__name__)

def funcion_aux_comprobar_ack(conn, codigo, sesion_id, sensor_id, texto, nivel):
        # Checkear que si hay un alerta con ese codigo (devuelve [alarma_id, reconocimeinto])
        ack_alerta = database.find_reconocimiento_alerta_por_codigo_en_sesion(conn, codigo, sesion_id)
        
        if ack_alerta == None or not ack_alerta[1]:
            id_nueva_alerta = database.insert_alerta(conn, sensor_id, texto, codigo, nivel, sesion_id)
            demo_mostrar_popup_externo(id_nueva_alerta, texto, codigo)
     
     

def funcion_dos_umbrales_max(conn, umbral_aviso, umbral_alarma, unidad, sensor_id, value, sesion_id):
        # AVISOS AV Y ALARMAS AL; SENSOR_ID; 
        if umbral_aviso < value and value <= umbral_alarma:
            nivel='AVISO'
            codigo = f'{nivel[:2]}{sensor_id}X'
            texto_aviso = f"[{nivel}] Valores de '{sensor_id}' altos > {umbral_aviso}{unidad} ({value}{unidad})"
            funcion_aux_comprobar_ack(conn, codigo, sesion_id, sensor_id, texto_aviso, nivel)

        elif value > umbral_alarma:
            nivel='ALARMA'
            codigo = f'{nivel[:2]}{sensor_id}X'
            texto_alarma = f"[{nivel}] NIVELES DE '{sensor_id}' PERJUDICIALES > {umbral_alarma}{unidad} ({value}{unidad})"
            funcion_aux_comprobar_ack(conn, codigo, sesion_id, sensor_id, texto_alarma, nivel)


def funcion_dos_umbrales_min(conn, umbral_aviso, umbral_alarma, unidad, sensor_id, value, sesion_id):
        # AVISOS AV Y ALARMAS AL; SENSOR_ID; 
        if umbral_alarma <= value and value < umbral_aviso:
            nivel='AVISO'
            codigo = f'{nivel[:2]}{sensor_id}N'
            texto_aviso = f"[{nivel}] Valores de '{sensor_id}' bajos < {umbral_aviso}{unidad} ({value}{unidad})"
            funcion_aux_comprobar_ack(conn, codigo, sesion_id, sensor_id, texto_aviso, nivel)

        elif value < umbral_alarma:
            nivel='ALARMA'
            codigo = f'{nivel[:2]}{sensor_id}N'
            texto_alarma = f"[{nivel}] NIVELES DE '{sensor_id}' PERJUDICIALES < {umbral_alarma}{unidad} ({value}{unidad})"
            funcion_aux_comprobar_ack(conn, codigo, sesion_id, sensor_id, texto_alarma, nivel)

def funcion_detectar(conn, sensor_id, value, sesion_id):
    if value>0:
        nivel='ALARMA'
        codigo = f'{nivel[:2]}{sensor_id}M'
        texto_alarma = f"[{nivel}] MANIPULACION DEL DISPOSITIVO DETECTADO POR '{sensor_id}'"
        funcion_aux_comprobar_ack(conn, codigo, sesion_id, sensor_id, texto_alarma, nivel)

def procesar_datos_sensor(conn, sensor_id, value, sesion_id):
    if sensor_id == "tem":
        unidad="ºC"
        funcion_dos_umbrales_max(conn, UMBRAL_AVISO_TEM_MAX, UMBRAL_ALARMA_TEM_MAX, unidad, sensor_id, value, sesion_id)
        funcion_dos_umbrales_min(conn, UMBRAL_AVISO_TEM_MIN, UMBRAL_ALARMA_TEM_MIN, unidad, sensor_id, value, sesion_id)

    elif sensor_id == "son":
        unidad="ADC"
        funcion_dos_umbrales_max(conn, UMBRAL_AVISO_SON_MAX, UMBRAL_ALARMA_SON_MAX, unidad, sensor_id, value, sesion_id)
    
    elif sensor_id == "hum":
        unidad="%"
        funcion_dos_umbrales_max(conn, UMBRAL_AVISO_HUM_MAX, UMBRAL_ALARMA_HUM_MAX, unidad, sensor_id, value, sesion_id)

    elif sensor_id == "luz":
        unidad=""
        funcion_dos_umbrales_min(conn, UMBRAL_AVISO_LUZ_MIN, UMBRAL_ALARMA_LUZ_MIN, unidad, sensor_id, value, sesion_id)

    elif sensor_id == "vib":
        funcion_detectar(conn, sensor_id, value, sesion_id)

    elif sensor_id == "gas":
        funcion_detectar(conn, sensor_id, value, sesion_id)


def demo_mostrar_popup_externo(alerta_id, texto_aviso, codigo):
    script = ("""
import tkinter as tk
import sys
import traceback
import logging
              

logger = logging.getLogger(__name__)

alerta_id = int(sys.argv[1])
texto = sys.argv[2]
codigo = sys.argv[3]
path = sys.argv[4]

sys.path.insert(0, path+'/src')
import database

    
log_file = f"{path}/logs/main.log"

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)-s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

def marcar():
    try:
        database.init_pool()
        conn = database.get_conn()
        database.update_reconocimiento_alerta(conn, alerta_id, True)
        logger.info(f"[DATABASE] No volveran a aparecer alertas de TIPO [{codigo}]")
        database.put_conn(conn)
        database.close_all()
    except Exception:
        traceback.print_exc()
    finally:
        root.destroy()

root = tk.Tk()
level = codigo[:2]
if level == 'AL':
    accent_bg = '#f8d7da'
    accent_fg = '#842029'
    title_prefix = 'ALARMA'
elif level == 'AV':
    accent_bg = '#fff3cd'
    accent_fg = '#664d03'
    title_prefix = 'AVISO'
else:
    accent_bg = '#e2e3e5'
    accent_fg = '#41464b'
    title_prefix = 'INFO'

root.title(f'{title_prefix} (Código: {codigo})')
root.geometry('520x240')
root.resizable(False, False)
root.attributes('-topmost', True)

banner = tk.Frame(root, bg=accent_bg, padx=16, pady=12)
banner.pack(fill='x')

tk.Label(
    banner,
    text=title_prefix,
    bg=accent_bg,
    fg=accent_fg,
    font=('Segoe UI', 10, 'bold')
).pack(anchor='w')

tk.Label(
    banner,
    text=f'Código: {codigo}',
    bg=accent_bg,
    fg=accent_fg,
    font=('Segoe UI', 9)
).pack(anchor='w')

frame = tk.Frame(root, padx=16, pady=16)
frame.pack(fill='both', expand=True)

message = tk.Label(frame, text=texto, wraplength=490, justify='left')
message.pack(fill='x', pady=(0, 12))

button_frame = tk.Frame(frame)
button_frame.pack(fill='x', pady=(8, 8))

tk.Button(button_frame, text='No volver a mostrar alertas para este código', command=marcar).pack(side='left', expand=True, fill='x', padx=(0, 6))
tk.Button(button_frame, text='OK', command=root.destroy).pack(side='left', expand=True, fill='x')

note = tk.Label(
    frame,
    text='La opción "No volver a mostrar alertas para este código" tomará efecto si se marca en la última alerta de ese código.',
    wraplength=490,
    justify='left',
    fg='#4a4a4a'
)
note.pack(fill='x', pady=(10, 0))

root.grab_set()
root.focus_force()
root.mainloop()
"""
    )
    subprocess.Popen([sys.executable, "-c", script, str(int(alerta_id)), texto_aviso, codigo, DEMO_PROJECT_PATH], close_fds=True)
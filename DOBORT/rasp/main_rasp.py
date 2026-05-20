import cv2
import numpy as np
import RPi.GPIO as GPIO
import time
import pydobot
from serial.tools import list_ports
import json
import serial
import threading
import queue

#Librería de rutinas del DOBOT
with open('rutinas.json', 'r', encoding='utf-8') as archivo: #modo read y pasamos los datos a utf-8
    rutinas = json.load(archivo)

#inicialización pines y puertos Rasp -----------------------------------------
PORT = "/dev/ttyAMA0"
GPIO.setmode(GPIO.BCM)
PINES_FT = {"ft1": 23, "ft2": 24, "ft3": 25, "ft4": 27, "ft5": 17, "ft6": 22}
for pin in PINES_FT.values():
    GPIO.setup(pin, GPIO.IN)

ser = serial.Serial('/dev/rfcomm0', 9600, timeout=0.1) # Ajusta el puerto: /dev/rfcomm0 si es BT clásico

#Cámara  --------------------------------------------------------------------
cap = cv2.VideoCapture(0)
lower_red1 = np.array([0,100,100])
upper_red1 = np.array([10,255,255])
lower_red2 = np.array([170,100,100])
upper_red2 = np.array([180,255,255])

lower_blue = np.array([100,100,100])
upper_blue = np.array([140,255,255])

lower_yellow = np.array([22,93,0])
upper_yellow = np.array([45,255,255])

#Estados (más fácil hacer una máquina de estados para el flujo) --------------
IDLE = "IDLE"
DETECTANDO = "DETECTANDO"
DECIDIENDO = "DECIDIENDO"
RUNNING = "RUNNING"
RECIBIR = "RECIBIR"
# -------------------------------------
estado = DETECTANDO
color_paquete = None
rutina_elegida = None
modo_actua = None #acomodar o recibir 

frames_threshold = 15 #frames viendo el mismo color para poder comprobar que es el paquete
contador_conf = 0
color_candidato = None

bt_queue = queue.Queue() #cola para las señales recibidas

#Módulos de bluetooth ---------------------------------------------------------
"""
Señales que recibe la RASP:
RL: SLAVE - Carrito llegó con paquete (modo acomodar)
RE: SLAVE - carrito en posición para recibir (modo recibir)
R1,...,R6: MASTER - no hay espacio disponible

Señales que envía la RASP:
K2: SLAVE - brazo tomó el pquete
KB: SLAVE - brazo terminó su rutina
ME: MASTER - no hay espacio disponible
"""
def bt_send(destino, dato):
    msg = (destino + dato).encode('ascii')
    ser.write(msg)
    print(f"[BT TX] → '{destino}{dato}'")

def receive_loop():
    """Hilo que escucha tramas entrantes del Slave."""
    while True:
        dest = ser.read(1)
        if not dest:
            continue
        dato = ser.read(1)
        if not dato:
            continue

        dest = dest.decode('ascii', errors='ignore')
        dato = dato.decode('ascii', errors='ignore')
        señal = dest + dato
        print(f"[BT RX] ← '{señal}'")
        bt_queue.put(señal)

#----------------------------------------------------------------------------
def leer_ft(nombre):
    if nombre in PINES_FT:
        return GPIO.input(PINES_FT[nombre])
    return 1 #si no existe asumimos que esta ocupado

def detectar_color(frame): #devuelve sólo el color
    #inicialización de cámara
    height, width, _= frame.shape
    roi = frame[int(height * 0.5):, :]
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    
    mask_red = (cv2.inRange(hsv, lower_red1, upper_red1)|cv2.inRange(hsv, lower_red2, upper_red2))
    mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)
    mask_yellow = cv2.inRange(hsv, lower_yellow,upper_yellow)

    areas = {
        "ROJO":     cv2.countNonZero(mask_red),
        "AZUL":     cv2.countNonZero(mask_blue),
        "AMARILLO": cv2.countNonZero(mask_yellow),
    }
    dominante = max(areas, key=areas.get)
    return dominante if areas[dominante] > 500 else "NONE", roi, areas

#rutinas ---------------------------------------------------------------------
#rutina en modo acomodar
def decidir_rutina_acomodar(color): #modo acomodar
    slots = {"ROJO": [("ft1", 1), ("ft4", 4)],
            "AZUL": [("ft2", 2), ("ft5", 5)],
            "AMARILLO": [("ft3", 3), ("ft6", 6)]}
    for ft_nombre, numero_rutina in slots[color]:
        valor = leer_ft(ft_nombre)
        print(f"[FT]{ft_nombre} = {valor} ({"libre" if valor == 0 else "ocupado"})")
        if valor == 0:
            return numero_rutina
    return None

#Para verificar si la casilla solicitada tiene un paquete (ft ocupado), devuele la rutina correspondiente o None
def verificar_rutina_recibir(numero):
    ft_por_rutina = {1: "ft1", 2: "ft2", 3: "ft3", 4: "ft4", 5: "ft5", 6: "ft6"}
    ft_nombre = ft_por_rutina.get(numero)
    if ft_nombre is None:
        return None
    valor = leer_ft(ft_nombre)
    print(f"[FT] {ft_nombre} = {valor} ({'ocupado' if valor == 1 else 'vacío'})")
    return numero if valor == 1 else None  # 1 = ocupado = hay paquete

def ejecutar_rutina_dobot(robot, numero):
    clave = str(numero)
    if clave not in rutinas:
        print(f"[ERROR] Rutina {clave} no encontrada en rutinas.json")
        return False
    puntos = rutinas[clave]
    print(f"[DOBOT] Ejecutando rutina {clave} ({len(puntos)} puntos)")
    for i, p in enumerate(puntos):
        print(f"  Punto {i}: x={p['x']} y={p['y']} z={p['z']} r={p['r']} suc={p['suction']}")
        robot.move_to(p['x'], p['y'], p['z'], p['r'], wait=True)
        try:
            robot.suck(enable=p['suction'])
        except TypeError:
            robot.suck(p['suction'])
        time.sleep(0.5)
    try:
        robot.suck(False)
    except Exception:
        pass
    print(f"[DOBOT] Rutina {clave} completada")
    return True

    return True

#Inicialización --------------------------------------------------------------
print("Sistema iniciado. Iniciando hilo Bluetooth")
t = threading.Thread(target=receive_loop, daemon=True)
t.start()

#conexión inicial al dobot
print("Conectando al Dobot Magician...")
robot = pydobot.Dobot(port=PORT, verbose= False) #verbose imprime en consola
print("¡Conectado!")
robot.speed(velocity=50, acceleration=50) #velocidad y aceleración van de 0 a 100
print("\n▶ Brazo a posición HOME")
robot.move_to(50, 25, 50, 0, wait=True)

#main loop -------------------------------------------------------------------
while True:
    while not bt_queue.empty():
    señal = bt_queue.get()
    print(f"[SYS] Procesando señal: '{señal}' | Estado: {estado}")

    # ── Señales del SLAVE ─────────────────────────────────────────────
    if señal == "RL" and estado == IDLE:
        modo_actual = "ACOMODAR"
        estado      = DETECTANDO
        print("[SYS] Modo ACOMODAR activado")

    elif señal == "RE" and estado == IDLE:
        modo_actual = "RECIBIR"
        estado      = RECIBIR
        print("[SYS] Modo RECIBIR → esperando posición del MASTER")

    # ── Señales del MASTER (R1…R6) ────────────────────────────────────
    # Separamos explícitamente para no confundir con RL o RE
    elif señal in ("R1","R2","R3","R4","R5","R6"):
        numero = int(señal[1])
        print(f"[SYS] Posición solicitada: {numero} | Estado actual: {estado}")

        if estado != RECIBIR:
            # RE y R1-R6 llegaron casi juntos, forzamos el estado
            print("[SYS] R1-R6 llegó antes de procesar RE, corrigiendo estado...")
            modo_actual = "RECIBIR"
            estado      = RECIBIR

        rutina_valida = verificar_rutina_recibir(numero)
        if rutina_valida is not None:
            rutina_elegida = rutina_valida
            estado         = RUNNING
            print(f"[SYS] Casilla {numero} tiene paquete → rutina {rutina_elegida}")
        else:
            print(f"[SYS] Casilla {numero} vacía → ME al MASTER")
            bt_send('M', 'E')
            estado      = IDLE
            modo_actual = None

    #Maquina de estados ------------------------------------------------------
    if estado == DETECTANDO:
        if color_detectado != "NONE":
            if color_detectado == color_candidato:
                contador_conf += 1 #para sumarle a la confirmación
            else:
                color_candidato = color_detectado
                contador_conf = 1
            if contador_conf >= frames_threshold:
                color_paquete = color_candidato
                estado = DECIDIENDO
                contador_conf = 0
                color_candidato = None
                print(f"[CAM] Color confirmado → {color_paquete}")
        else:
            # Ningún color visible → reinicia
            color_candidato  = None
            contador_conf = 0

    # decidiendo
    elif estado == DECIDIENDO:
        rutina_elegida = decidir_rutina_acomodar(color_paquete)
        if rutina_elegida is not None:
            print(f"[SYS] Espacio disponible → rutina {rutina_elegida}")
            estado = RUNNING
        else:
            bt_send('M', 'E') # MASTER: no hay espacio
            color_paquete = None
            estado = IDLE

    # llamar al brazo y regresar a IDL
    elif estado == RUNNING:
        ok = ejecutar_rutina_dobot(robot, rutina_elegida)
        if ok:
            if modo_actual == "ACOMODAR":
                bt_send('K', '2') # K2 a SLAVE: brazo tomó el paquete
                bt_send('K', 'B') # KB a SLAVE: brazo terminó rutina
            elif modo_actual == "RECIBIR":
                bt_send('K', 'B')   # KB → SLAVE: brazo terminó rutina
        rutina_elegida = None
        color_paquete  = None
        modo_actual    = None
        estado         = IDLE
        print("estado IDLE")

    #user interface
    estado_txt = f"Estado: {estado}"
    color_txt  = f"Color: {color_detectado}  (candidato: {color_candidato} x{contador_conf })"
    cv2.putText(roi, estado_txt, (10, 30),  cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
    cv2.putText(roi, color_txt,  (10, 60),  cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200,200,0),   2)
    cv2.imshow("Deteccion", roi)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
robot.move_to(50, 25, 50, wait=True)
ser.close()
cap.release()
cv2.destroyAllWindows()
GPIO.cleanup()           
           
    
    

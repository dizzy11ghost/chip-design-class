import cv2
import numpy as np
import RPi.GPIO as GPIO
import time
import pydobot
import json
import serial
import threading
import queue

# Rutinas del dobot
with open('rutinas.json', 'r', encoding='utf-8') as archivo:
    rutinas = json.load(archivo)

# configuración de pines GPIO
PORT = "/dev/ttyAMA0" 
GPIO.setmode(GPIO.BCM)
PINES_FT = {
    "ft1": 5,
    "ft2": 6,
    "ft3": 13,
    "ft4": 19,
    "ft5": 26,
    "ft6": 16
}
for pin in PINES_FT.values():
    GPIO.setup(pin, GPIO.IN)

# Bluetooth
ser = serial.Serial('/dev/rfcomm0', 9600, timeout=0.1)

# filtro de color para la cámara
cap = cv2.VideoCapture(0)
lower_red1   = np.array([0,   100, 100]); upper_red1   = np.array([10,  255, 255])
lower_red2   = np.array([170, 100, 100]); upper_red2   = np.array([180, 255, 255])
lower_blue   = np.array([100, 100, 100]); upper_blue   = np.array([140, 255, 255])
lower_yellow = np.array([22,  93,  0  ]); upper_yellow = np.array([45,  255, 255])

# Estados
IDLE       = "IDLE"
DETECTANDO = "DETECTANDO" #la cámara detecta qué paquete y qué color, para modo acomodar
DECIDIENDO = "DECIDIENDO"
RUNNING    = "RUNNING"
RECIBIR    = "RECIBIR"
ESPERANDO_RE = "ESPERANDO_RE" #espera la señal R1-R6 para decidir qué rutina ejecutar, para modo recibir

estado         = IDLE
color_paquete  = None
rutina_elegida = None
modo_actual    = None   # "ACOMODAR" | "RECIBIR"
posicion_pendiente = None #Para guardar el valor de R1-R6 que llega antes de decidir el modo, para no perder esa información si llega antes de tiempo

FRAMES_THRESHOLD  = 20
contador_conf     = 0
color_candidato   = None

bt_queue = queue.Queue()

# Bluetooth -------------------------------------------------------------------
def bt_send(destino, dato):
    msg = (destino + dato).encode('ascii')
    ser.write(msg)
    print(f"[BT TX] → '{destino}{dato}'")

def receive_loop():
    while True:
        dest = ser.read(1)
        if not dest:
            continue
        dato = ser.read(1)
        if not dato:
            continue
        dest  = dest.decode('ascii', errors='ignore')
        dato  = dato.decode('ascii', errors='ignore')
        señal = dest + dato
        print(f"[BT RX] ← '{señal}'")
        bt_queue.put(señal)

# Funciones auxiliares ------------------------------------------------------
def leer_ft(nombre):
    if nombre in PINES_FT:
        return GPIO.input(PINES_FT[nombre])
    return 0  # asume libre si no existe

def detectar_color(frame):
    height, width, _ = frame.shape
    roi = frame[int(height * 0.5):, :]
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    mask_red    = (cv2.inRange(hsv, lower_red1, upper_red1) |
                   cv2.inRange(hsv, lower_red2, upper_red2))
    mask_blue   = cv2.inRange(hsv, lower_blue,   upper_blue)
    mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)
    areas = {
        "ROJO":     cv2.countNonZero(mask_red),
        "AZUL":     cv2.countNonZero(mask_blue),
        "AMARILLO": cv2.countNonZero(mask_yellow),
    }
    dominante = max(areas, key=areas.get)
    return (dominante if areas[dominante] > 500 else "NONE"), roi

def decidir_rutina_acomodar(color): #para modo acomodar
    slots = {
        "ROJO":     [("ft1", 1), ("ft4", 4)],
        "AZUL":     [("ft2", 2), ("ft5", 5)],
        "AMARILLO": [("ft3", 3), ("ft6", 6)],
    }
    for ft_nombre, numero_rutina in slots[color]:
        valor = leer_ft(ft_nombre)
        print(f"[FT] {ft_nombre} = {valor} ({'libre' if valor == 0 else 'ocupado'})")
        if valor == 0:
            return numero_rutina
    return None

def verificar_rutina_recibir(numero):
    ft_por_rutina = {1:"ft1", 2:"ft2", 3:"ft3", 4:"ft4", 5:"ft5", 6:"ft6"}
    ft_nombre = ft_por_rutina.get(numero)
    if ft_nombre is None:
        return None
    valor = leer_ft(ft_nombre)
    print(f"[FT] {ft_nombre} = {valor} ({'ocupado' if valor == 1 else 'vacío'})")
    return numero if valor == 1 else None

def ejecutar_rutina_dobot(robot, numero): #cuando recibe RL o RE
    clave = str(numero)
    if clave not in rutinas:
        print(f"[ERROR] Rutina {clave} no encontrada")
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

# Inicialización -------------------------------------------------------------
print("[SYS] Iniciando hilo Bluetooth...")
threading.Thread(target=receive_loop, daemon=True).start()

print("[SYS] Conectando al Dobot Magician...")
robot = pydobot.Dobot(port=PORT, verbose=False)
print("[SYS] ¡Conectado!")
#robot.speed(velocity=50, acceleration=50)
#print("[SYS] Brazo a posición HOME")
#robot.move_to(250, 25, 50, 0, wait=True)
print("Esperando señal BT...")

# ── Main loop ─────────────────────────────────────────────────────────────────
frame, ret = cap.read()
roi            = None
color_detectado = "NONE"

while True:

    # Señales BT -------------------------------------------------------------
    while not bt_queue.empty():
        señal = bt_queue.get()
        print(f"Señal recibida: '{señal}' | Estado: {estado}")

        if señal == "RL" and estado == IDLE: #RL es para acomodar, RE es para recibir
            modo_actual = "ACOMODAR"
            estado      = DETECTANDO
            print("[SYS] Modo ACOMODAR →cámara detectando color del paquete")

        elif señal == "RE" and estado == IDLE:
            if estado == IDLE:
                # RE llegó primero, esperamos R1-R6
                modo_actual = "RECIBIR"
                estado      = RECIBIR
                print("Modo RECIBIR activado → esperando R1-R6 del MASTER...")
            elif estado == ESPERANDO_RE:
                # R1-R6 ya llegó antes que RE, ahora sí podemos ejecutar
                print(f"RE recibido, posición elegida: {posicion_pendiente} → ejecutando rutina")
                modo_actual = "RECIBIR"
                rutina_valida = verificar_rutina_recibir(posicion_pendiente)
                if rutina_valida is not None:
                    rutina_elegida     = rutina_valida
                    posicion_pendiente = None
                    estado             = RUNNING
                    print(f"Casilla {rutina_elegida} ocupada → iniciando rutina {rutina_elegida}")
                    bt_send('M', 'N')

                else:
                    print(f"[SYS] Casilla {posicion_pendiente} vacía → ME al MASTER")
                    bt_send('M', 'N')
                    posicion_pendiente = None
                    modo_actual        = None
                    estado             = IDLE

        elif señal in ("R1","R2","R3","R4","R5","R6"):
            numero = int(señal[1])
            print(f"[BT] Posición solicitada: {numero} | Estado: {estado}")

            if estado in (RECIBIR, IDLE, ESPERANDO_RE):
                # primero verificamos si hay paquete en esa casilla
                rutina_valida = verificar_rutina_recibir(numero)

                if rutina_valida is not None:
                    # hay paquete → avisamos al MASTER y esperamos RE del SLAVE
                    print(f"[SYS] Casilla {numero} tiene paquete → MS al MASTER")
                    bt_send('M', 'S')          # MS → MASTER: hay paquete
                    posicion_pendiente = numero
                    modo_actual        = "RECIBIR"

                    if estado == RECIBIR:
                        # RE ya llegó antes → ejecutar directo
                        print("[SYS] RE ya estaba → ejecutando rutina directamente")
                        rutina_elegida     = rutina_valida
                        posicion_pendiente = None
                        estado             = RUNNING
                    else:
                        # esperamos RE del SLAVE para confirmar que el carrito está listo
                        estado = ESPERANDO_RE
                        print(f"[SYS] Esperando RE del SLAVE para ejecutar rutina {numero}...")

                else:
                    # no hay paquete → avisamos al MASTER
                    print(f"[SYS] Casilla {numero} vacía → MN al MASTER")
                    bt_send('M', 'N')          # MN → MASTER: no hay paquete
                    posicion_pendiente = None
                    modo_actual        = None
                    estado             = IDLE
            else:
                print(f"[WARN] R{numero} en estado inesperado: {estado}, ignorando")

        elif señal == "RE":
            if estado == IDLE:
                modo_actual = "RECIBIR"
                estado      = RECIBIR
                print("[SYS] RE recibido → esperando R1-R6 del MASTER...")

            elif estado == ESPERANDO_RE:
                # teníamos posición pendiente, ahora el carrito confirmó que está listo
                print(f"[SYS] RE recibido, ejecutando rutina pendiente: {posicion_pendiente}")
                rutina_valida = verificar_rutina_recibir(posicion_pendiente)
                if rutina_valida is not None:
                    rutina_elegida     = rutina_valida
                    posicion_pendiente = None
                    estado             = RUNNING
                    print(f"[SYS] Iniciando rutina {rutina_elegida}")
                else:
                    print(f"[SYS] Casilla ya no tiene paquete → MN al MASTER")
                    bt_send('M', 'N')
                    posicion_pendiente = None
                    modo_actual        = None
                    estado             = IDLE
            else:
                print(f"[WARN] RE en estado inesperado: {estado}, ignorando")

    # Leer cámara (siempre, para mantener el buffer fresco)
    if ret and frame is not None:
        color_detectado, roi = detectar_color(frame)
    else:
        time.sleep(0.05)

    # Máquina de estados ------------------------------------------------------
    if estado == DETECTANDO: #sólo llamamod a detectando cuando el modo es acomodar, porque ahí es cuando la cámara tiene que detectar el color del paquete para decidir la rutina. En recibir no importa el color, sólo la posición del MASTER
        if color_detectado != "NONE":
            if color_detectado == color_candidato:
                contador_conf += 1 #contador_conf es para el threshold de frames para confirmar el color
            else:
                color_candidato = color_detectado
                contador_conf   = 1
            if contador_conf >= FRAMES_THRESHOLD:
                color_paquete   = color_candidato
                estado          = DECIDIENDO
                contador_conf   = 0
                color_candidato = None
                print(f"Color confirmado → {color_paquete}")
        else:
            color_candidato = None
            contador_conf   = 0

    elif estado == DECIDIENDO: #decide qué rutina usar para acomodar, dependiendo del color detectado. Si el modo es recibir, no se decide rutina, se espera la señal R1-R6 para decidir la rutina
        rutina_elegida = decidir_rutina_acomodar(color_paquete)
        if rutina_elegida is not None:
            print(f"[SYS] Slot libre → rutina {rutina_elegida}")
            estado = RUNNING
        else:
            print("[SYS] Sin espacio → ME al MASTER")
            bt_send('M', 'E')
            color_paquete = None
            modo_actual   = None
            estado        = IDLE

    elif estado == RUNNING:
        print(f"[SYS] Iniciando ejecución → rutina {rutina_elegida} | Modo: {modo_actual}")
        ok = ejecutar_rutina_dobot(robot, rutina_elegida)
        if ok:
            if modo_actual == "ACOMODAR":
                bt_send('K', '2')   # brazo tomó el paquete
                bt_send('K', 'B')   # brazo terminó rutina
            elif modo_actual == "RECIBIR":
                bt_send('K', 'B')   # brazo terminó rutina
        rutina_elegida  = None
        color_paquete   = None
        modo_actual     = None
        color_detectado = "NONE"    # evita re-detección inmediata
        estado          = IDLE
        print("[SYS] → IDLE")

    # 4. UI 
    if roi is not None:
        cv2.putText(roi, f"Estado: {estado} | Modo: {modo_actual}",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)
        cv2.putText(roi, f"Color: {color_detectado} | Cand: {color_candidato} x{contador_conf}",
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200,200,0), 2)
        cv2.imshow("Deteccion", roi)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
robot.move_to(50, 25, 50, 0, wait=True)
ser.close()
cap.release()
cv2.destroyAllWindows()
GPIO.cleanup()

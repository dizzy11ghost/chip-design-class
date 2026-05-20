import cv2
import numpy as np
import RPi.GPIO as GPIO
import time
import pydobot
import json
import serial
import threading
import queue

# ── Rutinas del DOBOT ─────────────────────────────────────────────────────────
with open('rutinas.json', 'r', encoding='utf-8') as archivo:
    rutinas = json.load(archivo)

# ── GPIO ──────────────────────────────────────────────────────────────────────
PORT = "/dev/ttyAMA0"
GPIO.setmode(GPIO.BCM)
PINES_FT = {"ft1": 23, "ft2": 24, "ft3": 25, "ft4": 27, "ft5": 17, "ft6": 22}
for pin in PINES_FT.values():
    GPIO.setup(pin, GPIO.IN)

# ── Bluetooth ─────────────────────────────────────────────────────────────────
ser = serial.Serial('/dev/rfcomm0', 9600, timeout=0.1)

# ── Cámara ────────────────────────────────────────────────────────────────────
cap = cv2.VideoCapture(0)
lower_red1   = np.array([0,   100, 100]); upper_red1   = np.array([10,  255, 255])
lower_red2   = np.array([170, 100, 100]); upper_red2   = np.array([180, 255, 255])
lower_blue   = np.array([100, 100, 100]); upper_blue   = np.array([140, 255, 255])
lower_yellow = np.array([22,  93,  0  ]); upper_yellow = np.array([45,  255, 255])

# ── Estados ───────────────────────────────────────────────────────────────────
IDLE       = "IDLE"
DETECTANDO = "DETECTANDO"
DECIDIENDO = "DECIDIENDO"
RUNNING    = "RUNNING"
RECIBIR    = "RECIBIR"

estado         = IDLE
color_paquete  = None
rutina_elegida = None
modo_actual    = None   # "ACOMODAR" | "RECIBIR"

FRAMES_THRESHOLD  = 15
contador_conf     = 0
color_candidato   = None

bt_queue = queue.Queue()

# ── Bluetooth ─────────────────────────────────────────────────────────────────
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

# ── Helpers ───────────────────────────────────────────────────────────────────
def leer_ft(nombre):
    if nombre in PINES_FT:
        return GPIO.input(PINES_FT[nombre])
    return 1  # asume ocupado si no existe

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

def decidir_rutina_acomodar(color):
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

def ejecutar_rutina_dobot(robot, numero):
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

# ── Inicialización ────────────────────────────────────────────────────────────
print("[SYS] Iniciando hilo Bluetooth...")
threading.Thread(target=receive_loop, daemon=True).start()

print("[SYS] Conectando al Dobot Magician...")
robot = pydobot.Dobot(port=PORT, verbose=False)
print("[SYS] ¡Conectado!")
robot.speed(velocity=50, acceleration=50)
print("[SYS] Brazo a posición HOME")
robot.move_to(50, 25, 50, 0, wait=True)
print("[SYS] Listo. Esperando señal BT...")

# ── Main loop ─────────────────────────────────────────────────────────────────
roi            = None
color_detectado = "NONE"

while True:

    # 1. Señales BT — siempre primero, sin bloquear ───────────────────────────
    while not bt_queue.empty():
        señal = bt_queue.get()
        print(f"[SYS] Señal recibida: '{señal}' | Estado: {estado}")

        if señal == "RL" and estado == IDLE:
            modo_actual = "ACOMODAR"
            estado      = DETECTANDO
            print("[SYS] Modo ACOMODAR → DETECTANDO")

        elif señal == "RE" and estado == IDLE:
            modo_actual = "RECIBIR"
            estado      = RECIBIR
            print("[SYS] Modo RECIBIR → esperando posición del MASTER")

        elif señal in ("R1","R2","R3","R4","R5","R6"):
            numero = int(señal[1])
            print(f"[SYS] Posición solicitada: {numero} | Estado: {estado}")
            # Tolerancia: RE y R1-R6 pueden llegar casi juntos
            if estado not in (RECIBIR, IDLE):
                print("[WARN] R1-R6 recibido en estado inesperado, ignorando")
            else:
                if estado == IDLE:
                    print("[SYS] Forzando modo RECIBIR por llegada anticipada")
                    modo_actual = "RECIBIR"
                    estado      = RECIBIR
                rutina_valida = verificar_rutina_recibir(numero)
                if rutina_valida is not None:
                    rutina_elegida = rutina_valida
                    estado         = RUNNING
                    print(f"[SYS] Casilla {numero} ocupada → rutina {rutina_elegida}")
                else:
                    print(f"[SYS] Casilla {numero} vacía → ME al MASTER")
                    bt_send('M', 'E')
                    estado      = IDLE
                    modo_actual = None

    # 2. Leer cámara (siempre, para mantener el buffer fresco) ────────────────
    ret, frame = cap.read()
    if ret and frame is not None:
        color_detectado, roi = detectar_color(frame)
    else:
        time.sleep(0.05)

    # 3. Máquina de estados ────────────────────────────────────────────────────
    if estado == DETECTANDO:
        if color_detectado != "NONE":
            if color_detectado == color_candidato:
                contador_conf += 1
            else:
                color_candidato = color_detectado
                contador_conf   = 1
            if contador_conf >= FRAMES_THRESHOLD:
                color_paquete   = color_candidato
                estado          = DECIDIENDO
                contador_conf   = 0
                color_candidato = None
                print(f"[CAM] Color confirmado → {color_paquete}")
        else:
            color_candidato = None
            contador_conf   = 0

    elif estado == DECIDIENDO:
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

    # 4. UI ───────────────────────────────────────────────────────────────────
    if roi is not None:
        cv2.putText(roi, f"Estado: {estado} | Modo: {modo_actual}",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)
        cv2.putText(roi, f"Color: {color_detectado} | Cand: {color_candidato} x{contador_conf}",
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200,200,0), 2)
        cv2.imshow("Deteccion", roi)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# ── Cleanup ───────────────────────────────────────────────────────────────────
robot.move_to(50, 25, 50, 0, wait=True)
ser.close()
cap.release()
cv2.destroyAllWindows()
GPIO.cleanup()

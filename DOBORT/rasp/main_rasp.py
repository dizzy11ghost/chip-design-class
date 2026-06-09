import cv2
import numpy as np
import RPi.GPIO as GPIO
import time
from pydobotplus import Dobot
import json
import serial
import threading
import os
import queue

# ── Rutinas ───────────────────────────────────────────────────────────────────
CARPETA_RUTINAS = "rutinas"

def cargar_rutinas_todas():
    rutinas = {}
    for i in range(1, 13):
        ruta = os.path.join(CARPETA_RUTINAS, f"rutina_{i:02d}.json")
        if os.path.exists(ruta):
            with open(ruta, "r", encoding="utf-8") as f:
                data = json.load(f)
            rutinas[f"{i:02d}"] = data.get("rutina", [])
            print(f"[RUTINAS] Cargada {ruta} → {len(rutinas[f'{i:02d}'])} puntos")
        else:
            print(f"[RUTINAS] No encontrada: {ruta}")
    return rutinas

rutinas = cargar_rutinas_todas()

# ── Config Dobot ──────────────────────────────────────────────────────────────
PORT                 = "/dev/ttyS0"
VELOCIDAD            = 100
ACELERACION          = 100
MODO_MOVIMIENTO      = 0x01
UMBRAL_DESVIACION_MM = 2.0

# ── GPIO ──────────────────────────────────────────────────────────────────────
GPIO.setmode(GPIO.BCM)
PINES_FT = {"ft1": 17, "ft4": 22, "ft3": 4, "ft2": 24, "ft6": 25, "ft5": 27}
for pin in PINES_FT.values():
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# ── Bluetooth ─────────────────────────────────────────────────────────────────
ser_master = serial.Serial('/dev/rfcomm1', 9600, timeout=0.1)
ser_carro  = serial.Serial('/dev/rfcomm0', 9600, timeout=0.1)

bt_queue_master = queue.Queue()
bt_queue_carro  = queue.Queue()

def bt_send(destino, *args):
    msg = ''.join(map(str, args))
    if destino == "master":
        ser_master.write(msg.encode())
        print(f"[BT TX → MASTER] '{msg}'")
    elif destino == "carro":
        ser_carro.write(msg.encode())
        print(f"[BT TX → CARRO] '{msg}'")

def receive_loop(ser, bt_queue, nombre):
    while True:
        dest = ser.read(1)
        if not dest:
            continue
        dato = ser.read(1)
        if not dato:
            continue
        señal = dest.decode('ascii', errors='ignore') + dato.decode('ascii', errors='ignore')
        print(f"[BT RX ← {nombre}] '{señal}'")
        bt_queue.put(señal)

# ── Cámara ────────────────────────────────────────────────────────────────────
cap = cv2.VideoCapture(0)
lower_red1   = np.array([0,   100, 100]); upper_red1   = np.array([10,  255, 255])
lower_red2   = np.array([170, 100, 100]); upper_red2   = np.array([180, 255, 255])
lower_blue   = np.array([100, 100, 100]); upper_blue   = np.array([140, 255, 255])
lower_yellow = np.array([10,  100, 100]); upper_yellow = np.array([25,  255, 255])

# ── Estados ───────────────────────────────────────────────────────────────────
IDLE         = "IDLE"
DETECTANDO   = "DETECTANDO"    # visión detectando color (ACOMODAR)
DECIDIENDO   = "DECIDIENDO"    # decidiendo rutina según color (ACOMODAR)
ESPERANDO_RL = "ESPERANDO_RL"  # KUB mandado, esperando RL del carro
RUNNING      = "RUNNING"       # ejecutando rutina Dobot
ESPERANDO_RR = "ESPERANDO_RR"  # KBU mandado, esperando RR del carro

estado             = IDLE
modo_actual        = None   # "ACOMODAR" | "RECIBIR"
color_paquete      = None
rutina_elegida     = None
posicion_pendiente = None
color_detectado    = "NONE"
FRAMES_THRESHOLD   = 20
contador_conf      = 0
color_candidato    = None

# ── Funciones auxiliares ──────────────────────────────────────────────────────
def leer_ft(nombre):
    return GPIO.input(PINES_FT[nombre]) if nombre in PINES_FT else 0

def detectar_color(frame):
    height, width, _ = frame.shape
    roi = frame[:int(height * 0.5), :]
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
        "ROJO":     [("ft1", 7),  ("ft4", 10)],
        "AZUL":     [("ft2", 8),  ("ft5", 11)],
        "AMARILLO": [("ft3", 9),  ("ft6", 12)],
    }
    for ft_nombre, numero_rutina in slots.get(color, []):
        valor = leer_ft(ft_nombre)
        print(f"[FT] {ft_nombre} = {valor} ({'libre' if valor == 0 else 'ocupado'})")
        if valor == 0:
            return numero_rutina
    return None

def verificar_rutina_recibir(numero):
    ft_por_rutina = {1: "ft1", 2: "ft2", 3: "ft3", 4: "ft4", 5: "ft5", 6: "ft6"}
    ft_nombre = ft_por_rutina.get(numero)
    if ft_nombre is None:
        return None
    valor = leer_ft(ft_nombre)
    print(f"[FT] {ft_nombre} = {valor} ({'ocupado' if valor == 1 else 'vacío'})")
    return numero if valor == 1 else None

# ── Funciones Dobot ───────────────────────────────────────────────────────────
def obtener_posicion_actual(robot):
    try:
        pose = robot.get_pose()
        if isinstance(pose, (tuple, list)):
            pose = pose[0]
        return {"x": pose.x, "y": pose.y, "z": pose.z, "r": pose.r}
    except Exception as e:
        print(f"  [WARN] No se pudo leer posición actual: {e}")
        return None

def calcular_desviacion(pos_real, punto_esperado):
    ejes   = ["x", "y", "z"]
    deltas = {eje: abs(pos_real[eje] - punto_esperado[eje]) for eje in ejes}
    return max(deltas.values()), deltas

def ejecutar_rutina_dobot(robot, numero):
    ruta = os.path.join(CARPETA_RUTINAS, f"rutina_{numero:02d}.json")
    if not os.path.exists(ruta):
        print(f"[ERROR] No existe {ruta}")
        return False
    with open(ruta, "r", encoding="utf-8") as f:
        data = json.load(f)
    puntos = data.get("rutina", [])
    if not puntos:
        print(f"[ERROR] Rutina {numero:02d} vacía")
        return False

    print(f"[DOBOT] Ejecutando rutina {numero:02d} ({len(puntos)} puntos)")
    try:
        robot.speed(velocity=VELOCIDAD, acceleration=ACELERACION)
    except Exception:
        pass

    try:
        p0 = puntos[0]
        robot.move_to(p0["x"], p0["y"], p0["z"], p0.get("r", 0),
                      wait=True, mode=MODO_MOVIMIENTO)
        time.sleep(0.4)
    except Exception as e:
        print(f"[ERROR] No se pudo mover al punto inicial: {e}")
        return False

    correcciones = 0
    try:
        for i, punto in enumerate(puntos):
            x   = punto["x"];  y = punto["y"]
            z   = punto["z"];  r = punto.get("r", 0)
            suc = punto.get("succion", False)

            if i > 0:
                for intento in range(3):
                    pos_real = obtener_posicion_actual(robot)
                    if pos_real is None:
                        break
                    desviacion, deltas = calcular_desviacion(pos_real, puntos[i - 1])
                    if desviacion <= UMBRAL_DESVIACION_MM:
                        print(f"  [{i+1}/{len(puntos)}] ✓ (Δmax:{desviacion:.1f}mm) "
                              f"→ X:{x} Y:{y} Z:{z} R:{r} Suc:{'SÍ' if suc else 'NO'}")
                        break
                    correcciones += 1
                    ant = puntos[i - 1]
                    print(f"  [CORRECCIÓN #{correcciones}] intento {intento+1}/3 "
                          f"Δx:{deltas['x']:.1f} Δy:{deltas['y']:.1f} Δz:{deltas['z']:.1f}mm")
                    robot.move_to(ant["x"], ant["y"], ant["z"],
                                  ant.get("r", 0), wait=True, mode=MODO_MOVIMIENTO)
                    time.sleep(0.3)
                else:
                    print(f"  [WARN] punto {i+1} no convergió, continuando...")
            else:
                print(f"  [{i+1}/{len(puntos)}] → X:{x} Y:{y} Z:{z} R:{r} "
                      f"Suc:{'SÍ' if suc else 'NO'}")

            robot.move_to(x, y, z, r, wait=True, mode=MODO_MOVIMIENTO)
            robot.suck(suc)
            time.sleep(0.3)

        print(f"[DOBOT] Rutina {numero:02d} completada ({correcciones} correcciones)")
        return True
    except Exception as e:
        print(f"[ERROR] Interrumpida en punto {i+1}: {e}")
        return False
    finally:
        try:
            robot.suck(False)
        except Exception:
            pass

# ── Inicialización ────────────────────────────────────────────────────────────
print("Iniciando hilos Bluetooth...")
threading.Thread(target=receive_loop,
                 args=(ser_master, bt_queue_master, "MASTER"), daemon=True).start()
threading.Thread(target=receive_loop,
                 args=(ser_carro,  bt_queue_carro,  "CARRO"),  daemon=True).start()

print("Conectando al Dobot Magician...")
robot = Dobot(port=PORT)
print("¡Conectado!")
print("Esperando señal BT...")

# ── Main loop ─────────────────────────────────────────────────────────────────
roi = None

while True:

    # 1. Cámara
    ret, frame = cap.read()
    if ret and frame is not None:
        color_detectado, roi = detectar_color(frame)
    else:
        time.sleep(0.05)
        continue

    # 2. Señales BT Master ────────────────────────────────────────────────────
    while not bt_queue_master.empty():
        señal = bt_queue_master.get()
        print(f"[BT MASTER] '{señal}' | Estado: {estado}")

        # ── MODO ACOMODAR ─────────────────────────────────────────────────────
        # Master manda RS para indicar que hay un paquete esperando ser acomodado
        if señal == "RS" and estado == IDLE:
            modo_actual = "ACOMODAR"
            estado      = DETECTANDO
            print("[SYS] ACOMODAR → analizando color del paquete")

        # ── MODO RECIBIR ──────────────────────────────────────────────────────
        # Master manda R1-R6 indicando qué paquete quiere retirar
        elif señal in ("R1", "R2", "R3", "R4", "R5", "R6") and estado == IDLE:
            numero        = int(señal[1])
            rutina_valida = verificar_rutina_recibir(numero)
            if rutina_valida is not None:
                bt_send("master", 'M', 'S')
                rutina_elegida     = rutina_valida
                posicion_pendiente = numero
                modo_actual        = "RECIBIR"
                bt_send("carro", "KUB")
                estado = ESPERANDO_RL
                print(f"[SYS] Casilla {numero} ocupada → KUB enviado, esperando RL")
            else:
                bt_send("master", 'M', 'N')
                print(f"[SYS] Casilla {numero} vacía → MN al master")

    # 3. Señales BT Carro ─────────────────────────────────────────────────────
    while not bt_queue_carro.empty():
        señal = bt_queue_carro.get()
        print(f"[BT CARRO] '{señal}' | Estado: {estado}")

        # RL → carro llegó al brazo y está listo
        if señal == "RL" and estado == ESPERANDO_RL:
            print("[SYS] Carro listo en brazo → ejecutando rutina")
            estado = RUNNING

        # RR → carro llegó al usuario, avisar al master según el modo
        elif señal == "RR" and estado == ESPERANDO_RR:
            if modo_actual == "ACOMODAR":
                bt_send("master", 'M', 'L')
                print("[SYS] Carro en usuario → ML al master")
            elif modo_actual == "RECIBIR":
                bt_send("master", 'M', 'R')
                print("[SYS] Carro en usuario → MR al master")
            rutina_elegida     = None
            color_paquete      = None
            modo_actual        = None
            posicion_pendiente = None
            color_detectado    = "NONE"
            estado             = IDLE
            print("[SYS] → IDLE")

        else:
            print(f"[WARN] '{señal}' del carro ignorado en estado {estado}")

    # 4. Máquina de estados ───────────────────────────────────────────────────

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
                print(f"[SYS] Color confirmado → {color_paquete}")
        else:
            color_candidato = None
            contador_conf   = 0

    elif estado == DECIDIENDO and modo_actual == "ACOMODAR":
        rutina_elegida = decidir_rutina_acomodar(color_paquete)
        if rutina_elegida is not None:
            print(f"[SYS] Slot libre → rutina {rutina_elegida} | KUB al carro")
            bt_send("carro", "KUB")
            estado = ESPERANDO_RL
        else:
            print("[SYS] Sin espacio → ME al master")
            bt_send("master", 'M', 'E')
            color_paquete = None
            modo_actual   = None
            estado        = IDLE

    elif estado == RUNNING:
        print(f"[SYS] Ejecutando rutina {rutina_elegida} | Modo: {modo_actual}")
        ok = ejecutar_rutina_dobot(robot, rutina_elegida)
        if ok:
            if modo_actual == "ACOMODAR":
                bt_send("master", 'M', 'L')
                print("[SYS] Rutina ACOMODAR ok → ML al master | KBU al carro")
            elif modo_actual == "RECIBIR":
                bt_send("master", 'M', 'R')
                print("[SYS] Rutina RECIBIR ok → MR al master | KBU al carro")
            bt_send("carro", "KBU")
            estado = ESPERANDO_RR
        else:
            print("[SYS] Rutina falló → IDLE")
            rutina_elegida     = None
            color_paquete      = None
            modo_actual        = None
            posicion_pendiente = None
            color_detectado    = "NONE"
            estado             = IDLE

    # 5. UI ───────────────────────────────────────────────────────────────────
    if frame is not None:
        h, w, _ = frame.shape
        roi_y = h // 2
        cv2.rectangle(frame, (0, 0), (w, roi_y), (224, 150, 211), 2)
        cv2.putText(frame, "ROI color", (5, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (224, 150, 211), 1)
        cv2.putText(frame, f"Estado: {estado} | Modo: {modo_actual}",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, f"Color: {color_detectado} | Cand: {color_candidato} x{contador_conf}",
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 0), 2)
        cv2.imshow("Deteccion", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# ── Cleanup ───────────────────────────────────────────────────────────────────
robot.move_to(50, 25, 50, 0, wait=True)
ser_master.close()
ser_carro.close()
cap.release()
cv2.destroyAllWindows()
GPIO.cleanup()

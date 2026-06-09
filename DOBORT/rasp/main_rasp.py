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

# Rutinas del dobot
CARPETA_RUTINAS = "rutinas"
def cargar_rutinas_todas():
    rutinas = {}
    for i in range(1, 13):
        ruta = os.path.join(CARPETA_RUTINAS, f"rutina_{i:02d}.json")
        if os.path.exists(ruta):
            with open(ruta, "r", encoding="utf-8") as f:
                data = json.load(f)
            rutinas[f"{i:02d}"] = data.get("rutina", [])
            print(f"cargada {ruta} con {len(rutinas[f'{i:02d}'])} puntos")
        else:
            print(f"rutina no encontrada: {ruta}")
    return rutinas

rutinas = cargar_rutinas_todas()

# ── Config Dobot ──────────────────────────────────────────────────────────────
VELOCIDAD            = 100
ACELERACION          = 100
MODO_MOVIMIENTO      = 0x01
UMBRAL_DESVIACION_MM = 2.0

# configuración de pines GPIO
PORT = "/dev/ttyS0" 
GPIO.setmode(GPIO.BCM)
PINES_FT = {"ft1": 17, "ft4": 22, "ft3": 4, "ft2": 24, "ft6": 25, "ft5": 27}
for pin in PINES_FT.values():
    GPIO.setup(pin, GPIO.IN)

# Bluetooth
ser_master = serial.Serial('/dev/rfcomm1', 9600, timeout=0.1)
ser_carro  = serial.Serial('/dev/rfcomm0', 9600, timeout=0.1)

bt_queue_master = queue.Queue()
bt_queue_carro  = queue.Queue()

# filtro de color para la cámara
cap = cv2.VideoCapture(0)
lower_red1   = np.array([0,   100, 100]); upper_red1   = np.array([10,  255, 255])
lower_red2   = np.array([170, 100, 100]); upper_red2   = np.array([180, 255, 255])
lower_blue   = np.array([100, 100, 100]); upper_blue   = np.array([140, 255, 255])
lower_yellow = np.array([10,  100, 100]); upper_yellow = np.array([25,  255, 255])

# Estados
IDLE = "IDLE"
ESPERANDO_RE = "ESPERANDO_RE"
ESPERANDO_RL = "ESPERANDO_RL"
DETECTANDO   = "DETECTANDO"
DECIDIENDO   = "DECIDIENDO"
RUNNING      = "RUNNING"

estado             = IDLE
modo_actual        = None
color_paquete      = None
rutina_elegida     = None
posicion_pendiente = None
FRAMES_THRESHOLD   = 20
contador_conf      = 0
color_candidato    = None
color_detectado    = "NONE"
bt_queue = queue.Queue()

# Bluetooth -------------------------------------------------------------------
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
                    robot.move_to(x, y, z, r, wait=True, mode=MODO_MOVIMIENTO)
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

def decidir_rutina_acomodar(color):
    slots = {
        "ROJO":     [("ft1", 7),  ("ft4", 10)],
        "AZUL":     [("ft2", 8),  ("ft5", 11)],
        "AMARILLO": [("ft3", 9),  ("ft6", 12)],
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

# Inicialización -------------------------------------------------------------
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
roi          = None

while True:
    ret, frame = cap.read()
    if ret and frame is not None:
        color_detectado, roi = detectar_color(frame)
    else:
        time.sleep(0.05)
        continue

    # Señales BT -------------------------------------------------------------
    # Señales BT Master
    while not bt_queue_master.empty():
        señal = bt_queue_master.get()
        print(f"[BT MASTER] '{señal}' | Estado: {estado}")
    
        if señal == "RL" and estado == IDLE:
            modo_actual = "ACOMODAR"
            estado      = DETECTANDO
            print("[SYS] Modo ACOMODAR → detectando color")
    
        elif señal in ("R1","R2","R3","R4","R5","R6"):
            if estado != IDLE:
                print(f"[WARN] {señal} ignorado, estado: {estado}")
                continue
            numero        = int(señal[1])
            rutina_valida = verificar_rutina_recibir(numero)
            if rutina_valida is not None:
                bt_send("master", 'M', 'S')
                posicion_pendiente = numero
                rutina_elegida     = rutina_valida
                modo_actual        = "RECIBIR"
                estado             = ESPERANDO_RE
                print(f"[SYS] Casilla {numero} ocupada → esperando RE")
            else:
                bt_send("master", 'M', 'N')
                print(f"[SYS] Casilla {numero} vacía")
    
        elif señal == "RE":
            if estado == ESPERANDO_RE:
                print(f"[SYS] RE recibido → mandando KUB al carro")
                bt_send("carro", "KUB")
                estado = ESPERANDO_RL  # ← espera confirmación del carro
            else:
                print(f"[WARN] RE ignorado, estado: {estado}")
    
    # Señales BT Carro  ← este loop faltaba
    while not bt_queue_carro.empty():
        señal = bt_queue_carro.get()
        print(f"[BT CARRO] '{señal}' | Estado: {estado}")
    
        if señal == "RL":  # carro llegó al brazo → ejecutar rutina
            if estado == ESPERANDO_RL:
                print("[SYS] Carro listo → ejecutando rutina")
                estado = RUNNING
            else:
                print(f"[WARN] RL ignorado, estado: {estado}")
    
        elif señal == "RR":  # carro llegó al usuario → avisar al master
            print("[SYS] Carro en usuario → avisando master")
            bt_send("master", 'M', 'L' if modo_actual == "ACOMODAR" else 'R')
            estado = IDLE
            print("[SYS] → IDLE")
            

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
            print(f"Slot libre → rutina {rutina_elegida}")
            bt_send("carro", "KUB")
            estado = RUNNING
        else:
            print("Sin espacio → ME al MASTER")
            bt_send("master", 'M', 'E')
            color_paquete = None
            modo_actual   = None
            estado        = IDLE
            
    elif estado == RUNNING:
        print(f"[SYS] Ejecutando rutina {rutina_elegida} | Modo: {modo_actual}")
        ok = ejecutar_rutina_dobot(robot, rutina_elegida)
        if ok:
            bt_send("carro", "KBU")  # solo manda KBU, master se avisa cuando llega RR
            print("[SYS] Rutina ok → mandando KBU, esperando RR")
        else:
            print("[SYS] Rutina falló → IDLE")
            estado = IDLE
        rutina_elegida     = None
        color_paquete      = None
        posicion_pendiente = None
        color_detectado    = "NONE"
        # modo_actual NO se limpia aquí, lo necesita el manejador de RR

    # 4. UI 
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

# Cleanup
robot.move_to(50, 25, 50, 0, wait=True)
ser_master.close()
ser_carro.close()
cap.release()
cv2.destroyAllWindows()
GPIO.cleanup()

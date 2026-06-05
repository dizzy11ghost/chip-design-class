import cv2
import numpy as np
import RPi.GPIO as GPIO
import time
from pydobotplus import Dobot
import json
import serial
import threading
import queue
import os
import math

# ── Configuración general ─────────────────────────────────────────────────────
PORT = "/dev/ttyS0"
GPIO.setmode(GPIO.BCM)

# ── Estados ───────────────────────────────────────────────────────────────────
IDLE     = "IDLE"
DETECTAR = "DETECTAR"
DECIDIR  = "DECIDIR"
NAVEGAR  = "NAVEGAR"
RUN      = "RUN"
ACOMODAR = "ACOMODAR"
RECIBIR  = "RECIBIR"

# ── ArUco config ──────────────────────────────────────────────────────────────
aruco_dict   = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_ARUCO_ORIGINAL)
aruco_params = cv2.aruco.DetectorParameters()
detector     = cv2.aruco.ArucoDetector(aruco_dict, aruco_params)
marker_length   = 0.06
pixel_size      = 1.12e-6
focal_length_px = 500
focal_length_m  = focal_length_px * pixel_size

ARUCO_CARRO   = 25
ARUCO_BRAZO   = 50
ARUCO_USUARIO = 10

# ── Navegación feedforward — parámetros ───────────────────────────────────────
#
# Tamaño físico del ArUco del carrito (metros).
# Mide de borde a borde del cuadro negro exterior del marcador impreso.
MARKER_SIZE_M = 0.06

# Resolución de la cámara — debe coincidir con lo que entrega VideoCapture.
FRAME_W = 640
FRAME_H = 480

# Matriz de cámara aproximada.
# Sin calibrar con tablero: focal ≈ max(w,h) funciona bien para ángulos <30°.
_f  = max(FRAME_W, FRAME_H)
CAMERA_MATRIX = np.array([
    [_f,  0,  FRAME_W / 2],
    [0,   _f, FRAME_H / 2],
    [0,   0,  1           ],
], dtype=np.float64)
DIST_COEFFS = np.zeros((4, 1), dtype=np.float64)

# Esquinas del marcador en su sistema de coordenadas local (3D).
# Origen en el centro, Z apunta hacia la cámara.
# Orden: top-left, top-right, bottom-right, bottom-left (igual que OpenCV).
_hm = MARKER_SIZE_M / 2
MARKER_CORNERS_3D = np.array([
    [-_hm,  _hm, 0],
    [ _hm,  _hm, 0],
    [ _hm, -_hm, 0],
    [-_hm, -_hm, 0],
], dtype=np.float64)

# Zona muerta: si |yaw| < este valor se considera "recto" → KAA
ANGULO_MUERTO_DEG = 6.0

# Tabla ángulo → comando de compensación PWM.
# Formato: (umbral_superior_deg, cmd_avanzar, cmd_reversa)
# Se evalúa de arriba hacia abajo; el primer umbral que supere el yaw gana.
#
# CÓMO AJUSTAR UMBRALES:
#   Corre el carrito con KAA y observa qué yaw reporta la consola cuando
#   llega torcido. Si llega 8° hacia la derecha con KAA, el umbral de KAB
#   debería estar en ~5° para que lo atrape antes.
TABLA_COMANDOS = [
    (-25.0,           "KBC", "KBC"),
    (-15.0,           "KBB", "KBB"),
    (-ANGULO_MUERTO_DEG, "KBA", "KBA"),
    ( ANGULO_MUERTO_DEG, "KAA", "KAA"),
    ( 15.0,           "KAB", "KAB"),
    ( 25.0,           "KAC", "KAC"),
    ( math.inf,       "KAD", "KAD"),
]

# Fracción del ancho del frame que define la zona de parking
PARKING_FRACCION = 0.125

# ── Rutinas del Dobot ─────────────────────────────────────────────────────────
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
VELOCIDAD           = 100
ACELERACION         = 100
MODO_MOVIMIENTO     = 0x01
UMBRAL_DESVIACION_MM = 2.0

# ── GPIO (finales de carrera) ─────────────────────────────────────────────────
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
    if areas[dominante] > 500:
        return dominante, roi
    return "NONE", roi

def detectar_arucos(frame):
    """
    Retorna (posiciones, corners_dict, frame).

    posiciones  : {id: (cx, cy, distance_z)}  — igual que antes
    corners_dict: {id: np.ndarray (4,2)}       — esquinas en píxeles para solvePnP
    """
    corners, ids, _ = detector.detectMarkers(frame)
    posiciones   = {}
    corners_dict = {}
    if ids is None:
        return posiciones, corners_dict, frame
    for i, marker_id in enumerate(ids.flatten()):
        pts      = corners[i].reshape((4, 2))
        width_px = np.linalg.norm(pts[1] - pts[0])
        width_m  = width_px * pixel_size
        distance_z = (focal_length_m * marker_length) / width_m if width_m > 0 else 0
        cx = int(np.mean(pts[:, 0]))
        cy = int(np.mean(pts[:, 1]))
        posiciones[marker_id]   = (cx, cy, distance_z)
        corners_dict[marker_id] = pts                   # ← nuevo

        pts_int = pts.astype(int)
        cv2.polylines(frame, [pts_int], True, (0, 255, 0), 2)
        cv2.putText(frame, f"ID:{marker_id}",
                    (pts_int[0][0], pts_int[0][1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (25, 255, 255), 1)
    return posiciones, corners_dict, frame

# ── Navegación feedforward ────────────────────────────────────────────────────

def _estimar_yaw(corners_2d: np.ndarray):
    """
    Estima el yaw del ArUco usando solvePnP y las esquinas en píxeles.

    Retorna yaw en grados, o None si solvePnP falla.

    Yaw ≈ 0°  → marcador mirando de frente a la cámara (carrito recto).
    Yaw > 0°  → girado a la derecha.
    Yaw < 0°  → girado a la izquierda.

    Si el ArUco está montado mirando hacia arriba (plano horizontal) el yaw
    corresponde directamente al ángulo de rumbo del carrito. Si las correcciones
    van al revés, negarlo aquí: return -yaw
    """
    ok, rvec, _ = cv2.solvePnP(
        MARKER_CORNERS_3D,
        corners_2d.reshape((4, 1, 2)),
        CAMERA_MATRIX,
        DIST_COEFFS,
        flags=cv2.SOLVEPNP_IPPE_SQUARE,
    )
    if not ok:
        return None
    R, _ = cv2.Rodrigues(rvec)
    sy = math.sqrt(R[0, 0]**2 + R[1, 0]**2)
    yaw = math.degrees(math.atan2(R[1, 0], R[0, 0])) if sy > 1e-6 else 0.0
    return yaw

def _elegir_comando(yaw: float, es_avanzar: bool) -> str:
    for umbral, cmd_av, cmd_rev in TABLA_COMANDOS:
        if yaw < umbral:
            return cmd_av if es_avanzar else cmd_rev
    return "KAA"

def verificar_llegada(posiciones: dict, id_carro: int, id_destino: int,
                       frame_w: int, frame_h: int) -> bool:
    """Retorna True cuando el carrito entra en la zona de parking del destino."""
    if id_carro not in posiciones:
        return False
    cx, cy, _ = posiciones[id_carro]
    parte  = frame_h // 6
    roa_y1 = 1 * parte
    roa_y2 = 2 * parte
    if not (roa_y1 <= cy < roa_y2):
        return False
    if id_destino == ARUCO_BRAZO:
        return cx < frame_w * PARKING_FRACCION
    else:
        return cx > frame_w * (1.0 - PARKING_FRACCION)

def arrancar_carrito(corners_dict: dict, destino_id: int, frame_w: int, frame_h: int) -> bool:
    """
    Estima el yaw del carrito con solvePnP, manda el offset de PWM y luego el arranque.

    Retorna True si se enviaron los comandos, False si el ArUco no era visible.
    """
    es_avanzar = (destino_id == ARUCO_BRAZO)

    if ARUCO_CARRO not in corners_dict:
        print("[NAV] ArUco del carrito no visible — no se puede estimar yaw")
        return False

    yaw = _estimar_yaw(corners_dict[ARUCO_CARRO])
    if yaw is None:
        print("[NAV] solvePnP falló — usando KAA por defecto")
        yaw = 0.0

    cmd_offset   = _elegir_comando(yaw, es_avanzar)
    cmd_arranque = "KUB" if es_avanzar else "KBU"

    print(f"[NAV] Yaw estimado: {yaw:.1f}° → offset: {cmd_offset} → arranque: {cmd_arranque}")

    # 1. Offset de PWM (KL25 lo guarda internamente, no arranca todavía)
    bt_send("carro", cmd_offset)
    time.sleep(0.05)   # gap mínimo para que el KL25 procese antes del arranque
    # 2. Arranque con PWM ya compensado
    bt_send("carro", cmd_arranque)
    return True

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

# ── Variables de estado ───────────────────────────────────────────────────────
estado         = IDLE
modo_actual    = None
color_paquete  = None
rutina_elegida = None
FRAMES_THRESHOLD = 20
contador_conf  = 0
color_candidato = None

nav_origen          = None
nav_referencia      = None
nav_signal          = None
nav_siguiente_estado = None

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
roi          = None
posiciones   = {}
corners_dict = {}   # esquinas ArUco para solvePnP

while True:
    ret, frame = cap.read()
    if ret and frame is not None:
        color_detectado, roi              = detectar_color(frame)
        posiciones, corners_dict, frame   = detectar_arucos(frame)
    else:
        time.sleep(0.05)
        continue

    # ── Señales BT ────────────────────────────────────────────────────────────
    while not bt_queue_master.empty():
        señal = bt_queue_master.get()
        print(f"Estado: {estado}")

        if señal == "RS" and estado == IDLE:
            modo_actual = ACOMODAR
            estado      = DETECTAR
            print("ACOMODAR iniciado")

        elif señal in ("R1","R2","R3","R4","R5","R6"):
            if estado != IDLE:
                continue
            numero = int(señal[1])
            rutina_valida = verificar_rutina_recibir(numero)
            if rutina_valida is not None:
                bt_send("master", 'M', 'S')
                rutina_elegida       = numero
                modo_actual          = RECIBIR
                nav_referencia       = ARUCO_BRAZO
                nav_siguiente_estado = RUN
                estado               = NAVEGAR
                # ← arranque feedforward: calcula yaw y manda offset+KUB
                arrancar_carrito(corners_dict, ARUCO_BRAZO,
                                 frame.shape[1], frame.shape[0])
                print(f"[FSM] NAVEGAR → RUN rutina {numero}")
            else:
                bt_send("master", 'M', 'N')
                print(f"casilla {numero} vacía, no se puede recibir ahí")

    # ── Máquina de estados ────────────────────────────────────────────────────
    if estado == DETECTAR:
        if color_detectado != "NONE":
            if color_detectado == color_candidato:
                contador_conf += 1
            else:
                color_candidato = color_detectado
                contador_conf   = 1
            if contador_conf >= FRAMES_THRESHOLD:
                color_paquete   = color_candidato
                estado          = DECIDIR
                contador_conf   = 0
                color_candidato = None
                print(f"Color confirmado → {color_paquete}")
        else:
            color_candidato = None
            contador_conf   = 0

    elif estado == DECIDIR:
        rutina_elegida = decidir_rutina_acomodar(color_paquete)
        if rutina_elegida is not None:
            print(f"[Slot libre → rutina {rutina_elegida}]")
            nav_referencia       = ARUCO_BRAZO
            nav_siguiente_estado = RUN
            estado               = NAVEGAR
            # ← arranque feedforward
            arrancar_carrito(corners_dict, ARUCO_BRAZO,
                             frame.shape[1], frame.shape[0])
        else:
            print("Sin espacio → ME al MASTER")
            bt_send("master", 'M', 'E')
            estado = IDLE

    elif estado == NAVEGAR:
        h, w, _ = frame.shape
        if verificar_llegada(posiciones, ARUCO_CARRO, nav_referencia, w, h):
            bt_send("carro", "KST")
            estado = nav_siguiente_estado
            destino_str = "BRAZO" if nav_referencia == ARUCO_BRAZO else "USUARIO"
            print(f"[FSM] LLEGADA a {destino_str} → {estado}")

    elif estado == RUN:
        print(f"[DEBUG] rutina_elegida={rutina_elegida} | modo={modo_actual}")
        ok = ejecutar_rutina_dobot(robot, rutina_elegida)
        if ok:
            if modo_actual == ACOMODAR:
                bt_send("master", 'M', 'L')
                nav_referencia       = ARUCO_USUARIO
                nav_siguiente_estado = IDLE
                estado               = NAVEGAR
                # ← arranque feedforward de regreso
                arrancar_carrito(corners_dict, ARUCO_USUARIO,
                                 frame.shape[1], frame.shape[0])
                print("[FSM] Paquete depositado → navegando a usuario")
            elif modo_actual == RECIBIR:
                bt_send("master", 'M', 'R')
                nav_referencia       = ARUCO_USUARIO
                nav_siguiente_estado = IDLE
                estado               = NAVEGAR
                # ← arranque feedforward de regreso
                arrancar_carrito(corners_dict, ARUCO_USUARIO,
                                 frame.shape[1], frame.shape[0])
                print("[FSM] Paquete tomado → navegando a usuario")
        else:
            estado = IDLE

    # ── UI de debug ───────────────────────────────────────────────────────────
    if frame is not None:
        h, w, _ = frame.shape
        parte    = h // 6
        roi_y    = h // 2
        roa_y1   = 1 * parte
        roa_y2   = 2 * parte
        pb_x2    = int(w * 0.125)
        pu_x1    = int(w * 0.875)

        cv2.rectangle(frame, (0, 0),    (w, roi_y),         (224, 150, 211), 2)
        cv2.rectangle(frame, (0, roa_y1),(w, roa_y2),       (178,  22,  26), 2)
        cv2.rectangle(frame, (0, roa_y1),(pb_x2, roa_y2),   (0,  128, 255),  2)
        cv2.rectangle(frame, (pu_x1, roa_y1),(w, roa_y2),   (255,   0, 128), 2)

        cv2.putText(frame, "ROI color", (5, roi_y + 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        cv2.putText(frame, "ROA carril", (5, roa_y1 + 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
        cv2.putText(frame, "PKB", (5, roa_y1 + 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 128, 255), 1)
        cv2.putText(frame, "PKU", (pu_x1 + 5, roa_y1 + 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 128), 1)
        cv2.putText(frame, f"Estado: {estado} | Modo: {modo_actual}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, f"Color: {color_detectado} | Cand: {color_candidato} x{contador_conf}",
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 0), 2)

        # Mostrar yaw en tiempo real cuando el carrito es visible
        if ARUCO_CARRO in corners_dict:
            yaw_live = _estimar_yaw(corners_dict[ARUCO_CARRO])
            if yaw_live is not None:
                cv2.putText(frame, f"Yaw carrito: {yaw_live:.1f}°", (10, 90),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 128), 2)

        if estado == NAVEGAR:
            destino_str = "BRAZO" if nav_referencia == ARUCO_BRAZO else "USUARIO"
            cv2.putText(frame, f"NAV destino: {destino_str}", (10, 115),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 200, 255), 2)

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

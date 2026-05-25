import cv2
import numpy as np
import RPi.GPIO as GPIO
import time
import pydobot
import json
import serial
import threading
import queue

#conf general ----------------------------------------------------
PORT = "/dev/ttyAMA0" 
GPIO.setmode(GPIO.BCM)

# Estados ------------------------------------------------------
IDLE     = "IDLE"
DETECTAR = "DETECTAR"
DECIDIR  = "DECIDIR"
NAVEGAR  = "NAVEGAR"
RUN      = "RUN"
#modos posibles
ACOMODAR = "ACOMODAR"
RECIBIR  = "RECIBIR"

#aruco config
aruco_dict   = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_ARUCO_ORIGINAL)
aruco_params = cv2.aruco.DetectorParameters()
detector     = cv2.aruco.ArucoDetector(aruco_dict, aruco_params)
marker_length   = 0.06    # metros (6 cm)
pixel_size      = 1.12e-6 # metros
focal_length_px = 500     # en pixeles
focal_length_m  = focal_length_px * pixel_size

# IDs de marcadores ArUco y umbral de llegada ------------------
ARUCO_CARRO   = 25
ARUCO_BRAZO   = 50
ARUCO_USUARIO = 10
DISTANCIA_LLEGADA_CM = 10.0  # cm — ajustar según pruebas

# Rutinas del dobot ---------------------------------------------
with open('rutinas.json', 'r', encoding='utf-8') as archivo:
    rutinas = json.load(archivo)

# configuración de pines GPIO ----------------------------------
PINES_FT = { "ft1": 17, "ft2": 22, "ft3": 23, "ft4": 24, "ft5": 25, "ft6": 27}
for pin in PINES_FT.values():
    GPIO.setup(pin, GPIO.IN)

# Bluetooth ----------------------------------------------------
ser_master = serial.Serial('/dev/rfcomm0', 9600, timeout=0.1)  # Master (comm0)
ser_carro  = serial.Serial('/dev/rfcomm1', 9600, timeout=0.1)  # Carro  (comm1)

bt_queue_master = queue.Queue()
bt_queue_carro  = queue.Queue()

"""
Señales que mandamos: 
al carro: KBU (distancia brazo usuario), KUB(distancia usuario brazo), distancia (3 valores cm)
master: MS (casilla ocupada), MN (casilla vacía), ME (sin espacio), ML (paquete depositado), MR(paquete mandado)
"""
def bt_send(destino, *args):
    msg = ''.join(map(str, args))
    if destino == "master":
        ser_master.write((msg + '\n').encode())
        print(f"[BT TX → MASTER] '{msg}'")
    elif destino == "carro":
        ser_carro.write((msg + '\n').encode())
        print(f"[BT TX → CARRO] '{msg}'")

#Señales que recibimos (sólo de Master): RS (start modo 1), R1-R6 (modo 2, posicion del slot)

def receive_loop(ser, bt_queue, nombre):
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
        print(f"[BT RX ← {nombre}] '{señal}'")
        bt_queue.put(señal)

#Cámara ------------------------------------------------------
cap = cv2.VideoCapture(0)
lower_red1   = np.array([0,   100, 100]); upper_red1   = np.array([10,  255, 255])
lower_red2   = np.array([170, 100, 100]); upper_red2   = np.array([180, 255, 255])
lower_blue   = np.array([100, 100, 100]); upper_blue   = np.array([140, 255, 255])
lower_yellow = np.array([22,  93,  0  ]); upper_yellow = np.array([45,  255, 255])

# Funciones auxiliares ------------------------------------------------------
def leer_ft(nombre):
    return GPIO.input(PINES_FT[nombre]) if nombre in PINES_FT else 0

def detectar_color(frame):
    height, width, _ = frame.shape
    roi = frame[int(height * 0.5):, :]
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    mask_red    = (cv2.inRange(hsv, lower_red1, upper_red1) | cv2.inRange(hsv, lower_red2, upper_red2))
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

def detectar_arucos(frame): #vectores de posición de los marcadores
    corners, ids, _ = detector.detectMarkers(frame)
    posiciones = {} #diccionario para guardar posiciones de cada ID
    if ids is None:          # FIX: antes retornaba aquí siempre, nunca procesaba markers
        return posiciones, frame
    for i, marker_id in enumerate(ids.flatten()): #enumerate para obtener índice a través de la iteración, flatten para convertir ids a 1D
        pts      = corners[i].reshape((4, 2)) #obtenemos las esquinas del marcador
        width_px = np.linalg.norm(pts[1] - pts[0]) #calculamos el ancho en pixeles
        width_m  = width_px * pixel_size #convertimos a metros
        distance_z = (focal_length_m * marker_length) / width_m #calculamos la distancia al marcador en eje Z
        cx = int(np.mean(pts[:, 0])) #saca el promedio de las coordenadas X de las esquinas para obtener el centro del marcador en X
        cy = int(np.mean(pts[:, 1]))
        posiciones[marker_id] = (cx, cy, distance_z) #vector diccionario que según el ID guarda posiciones y profundidad

        #dibujamos para UI
        pts_int = pts.astype(int)
        cv2.polylines(frame, [pts_int], True, (0, 255, 0), 2)
        cv2.putText(frame, f"ID:{marker_id} {distance_z:.2f}m",
                (pts_int[0][0], pts_int[0][1] - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 1)

    return posiciones, frame

def calcular_distancia(posiciones, origen_id, destino_id):
    if origen_id not in posiciones:
        return None
    if destino_id not in posiciones:
        return None
    p1 = posiciones[origen_id]
    p2 = posiciones[destino_id]
    distancia = abs(p1[2] - p2[2])
    return distancia

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

#note to self!!! Checar si esta calibración aproximada basta o hay que calibrar con un tablero de ajedrez para obtener coords 3D
estado         = IDLE
modo_actual    = None   # "ACOMODAR" | "RECIBIR"
color_paquete  = None
rutina_elegida = None
FRAMES_THRESHOLD = 20
contador_conf    = 0
color_candidato  = None

#navegación
nav_origen           = None
nav_destino          = None
nav_signal           = None
nav_siguiente_estado = None

# Inicialización -------------------------------------------------------------
print("Iniciando hilo Bluetooth...")
#threading
threading.Thread(target=receive_loop,
                 args=(ser_master, bt_queue_master, "MASTER"),
                 daemon=True).start()

threading.Thread(target=receive_loop,
                 args=(ser_carro,  bt_queue_carro,  "CARRO"),
                 daemon=True).start()
print("Conectando al Dobot Magician...")
robot = pydobot.Dobot(port=PORT, verbose=False)
print("¡Conectado!")
print("Esperando señal BT...")

# ── Main loop ─────────────────────────────────────────────────────────────────
roi       = None
posiciones = {}  # FIX: inicializar en scope del loop principal

while True:

    ret, frame = cap.read()
    # Leer cámara (siempre, para mantener el buffer fresco)
    if ret and frame is not None:
        color_detectado, roi = detectar_color(frame)
        posiciones, frame    = detectar_arucos(frame)  # FIX: actualizar posiciones cada frame
    else:
        time.sleep(0.05)
        continue

    # Señales BT -------------------------------------------------------------
    while not bt_queue_master.empty():
        señal = bt_queue_master.get()
        print(f"Estado: {estado}")

        #START ACOMODAR 
        if señal == "RS" and estado == IDLE: #RStart modo acomodar
            modo_actual = ACOMODAR
            estado      = DETECTAR
            print("ACOMODAR iniciado")

        #RECIBIR SLOT
        elif señal in ("R1","R2","R3","R4","R5","R6"):
            if estado != IDLE:
                continue
            numero = int(señal[1])
            rutina_valida = verificar_rutina_recibir(numero)
            if rutina_valida is not None:
                bt_send("master", 'M', 'S')
                rutina_elegida = numero
                modo_actual    = RECIBIR
                # FIX: modo RECIBIR navega carro→brazo primero, igual que ACOMODAR
                nav_origen           = ARUCO_CARRO
                nav_destino          = ARUCO_BRAZO
                nav_signal           = "KCB"
                nav_siguiente_estado = RUN
                estado               = NAVEGAR
                print(f"[FSM] NAVEGAR → RUN rutina {numero}")
            else:
                bt_send("master", 'M', 'N', '0')
                print(f"casilla {numero} vacía, no se puede recibir ahí")

    # Máquina de estados ------------------------------------------------------
    if estado == DETECTAR: #sólo llamamos a detectando cuando el modo es acomodar, porque ahí es cuando la cámara tiene que detectar el color del paquete para decidir la rutina
        if color_detectado != "NONE":
            if color_detectado == color_candidato:
                contador_conf += 1 #contador_conf es para el threshold de frames para confirmar el color
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

    elif estado == DECIDIR: #decide qué rutina usar para acomodar, dependiendo del color detectado
        rutina_elegida = decidir_rutina_acomodar(color_paquete)
        if rutina_elegida is not None:
            print(f"[Slot libre → rutina {rutina_elegida}")
            nav_origen           = ARUCO_CARRO
            nav_destino          = ARUCO_BRAZO
            nav_signal           = "KCB"
            nav_siguiente_estado = RUN
            estado               = NAVEGAR
        else:
            print("Sin espacio → ME al MASTER")
            bt_send("master", 'M', 'E')
            estado = IDLE

    elif estado == NAVEGAR:
        # FIX: posiciones ya están actualizadas arriba en cada frame
        distancia = calcular_distancia(posiciones, nav_origen, nav_destino)
        if distancia is not None:
            distancia_cm = distancia * 100
            print(f"[NAV] {distancia_cm:.1f} cm → señal {nav_signal}")
            bt_send("carro", nav_signal, f"{distancia_cm:.1f}")  # manda distancia cada frame hasta llegar

            if distancia_cm <= DISTANCIA_LLEGADA_CM:
                print("[NAV] Destino alcanzado")
                estado = nav_siguiente_estado
        # si no se ven los markers simplemente espera el siguiente frame

    elif estado == RUN:
        print(f"[SYS] Iniciando ejecución → rutina {rutina_elegida} | Modo: {modo_actual}")
        ok = ejecutar_rutina_dobot(robot, rutina_elegida)
        if ok:
            if modo_actual == ACOMODAR:
                # FIX: tras depositar, navegar brazo→usuario y avisar ML al master
                bt_send("master", 'M', 'L')
                nav_origen           = ARUCO_BRAZO
                nav_destino          = ARUCO_USUARIO
                nav_signal           = "KBU"
                nav_siguiente_estado = IDLE
                estado               = NAVEGAR
                print("[FSM] Paquete depositado → navegando a usuario")
            elif modo_actual == RECIBIR:
                # FIX: tras recoger, avisar MR al master y volver a IDLE
                bt_send("master", 'M', 'R')
                estado = IDLE
                print("[FSM] Paquete recogido → IDLE")
        else:
            estado = IDLE

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

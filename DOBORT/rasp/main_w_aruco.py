import cv2
import numpy as np
import RPi.GPIO as GPIO
import time
import pydobot
import json
import serial
import threading
import queue

#ARUCO ----------------------------------------------------
#aruco config
aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_ARUCO_ORIGINAL)
aruco_params = cv2.aruco.DetectorParameters()
detector = cv2.aruco.ArucoDetector(aruco_dict, aruco_params)
marker_length = 0.06   # metros (6 cm)
pixel_size = 1.12e-6   # metros
focal_length_px = 500  # en pixeles
focal_length_m = focal_length_px * pixel_size

# Rutinas del dobot ---------------------------------------------
with open('rutinas.json', 'r', encoding='utf-8') as archivo:
    rutinas = json.load(archivo)

# configuración de pines GPIO ----------------------------------
PORT = "/dev/ttyAMA0" 
GPIO.setmode(GPIO.BCM)
PINES_FT = { "ft1": 5, "ft2": 6, "ft3": 13, "ft4": 19, "ft5": 26, "ft6": 16}
for pin in PINES_FT.values():
    GPIO.setup(pin, GPIO.IN)

# Bluetooth ----------------------------------------------------
ser = serial.Serial('/dev/rfcomm0', 9600, timeout=0.1)
bt_queue = queue.Queue()

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


#Cámara ------------------------------------------------------
cap = cv2.VideoCapture(0)
lower_red1   = np.array([0,   100, 100]); upper_red1   = np.array([10,  255, 255])
lower_red2   = np.array([170, 100, 100]); upper_red2   = np.array([180, 255, 255])
lower_blue   = np.array([100, 100, 100]); upper_blue   = np.array([140, 255, 255])
lower_yellow = np.array([22,  93,  0  ]); upper_yellow = np.array([45,  255, 255])

# Estados ------------------------------------------------------
IDLE       = "IDLE"
DETECTANDO = "DETECTANDO" #la cámara detecta qué paquete y qué color, para modo acomodar
DECIDIENDO = "DECIDIENDO"
RUNNING    = "RUNNING"
RECIBIR    = "RECIBIR"
ESPERANDO_RE = "ESPERANDO_RE" #espera la señal R1-R6 para decidir qué rutina ejecutar, para modo recibir
NAVEGANDO = "NAVEGANDO" #Carrito en movimiento!! mandamos distancias por BT

estado         = IDLE
modo_actual    = None   # "ACOMODAR" | "RECIBIR"
color_paquete  = None
rutina_elegida = None
posicion_pendiente = None #Para guardar el valor de R1-R6 que llega antes de decidir el modo, para no perder esa información si llega antes de tiempo

FRAMES_THRESHOLD  = 20
contador_conf     = 0
color_candidato   = None

bt_queue = queue.Queue()

# Funciones auxiliares ------------------------------------------------------
def leer_ft(nombre):
    return GPIO.input(PINES_FT[nombre]) if nombre in PINES_FT else 0

def detectar_color(frame):
    height, width, _ = frame.shape
    roi = frame[int(height * 0.5):, :]
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    mask_red = (cv2.inRange(hsv, lower_red1, upper_red1) | cv2.inRange(hsv, lower_red2, upper_red2))
    mask_blue   = cv2.inRange(hsv, lower_blue,   upper_blue)
    mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)
    areas = {
        "ROJO": cv2.countNonZero(mask_red),
        "AZUL": cv2.countNonZero(mask_blue),
        "AMARILLO":cv2.countNonZero(mask_yellow),
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

def distancias_arucos(frame): #vectores de posición de los marcadores
    corners, ids, _ = detector.detectMarkers(frame)
    posiciones = {} #diccionario para guardar posiciones de cada ID
    if ids is not None:
        for i, marker_id in enumerate(ids.flatten()): #enumerate para obtener índice a través de la iteración, flatten para convertir ids a 1D
            pts = corners[i].reshape((4, 2)) #obtenemos las esquinas del marcador
            width_px = np.linalg.norm(pts[1] - pts[0]) #calculamos el ancho en pixeles
            width_m = width_px * pixel_size #convertimos a metros
            distance_z = (focal_length_m * marker_length) / width_m #calculamos la distancia al marcador en eje Z
            cx = int(np.mean(pts[:, 0])) #como funciona esto es que saca el promedio de las coordenadas X de las esquinas para obtener el centro del marcador en X, lo mismo para Y
            cy = int(np.mean(pts[:, 1]))
            posiciones[marker_id] = (cx, cy, distance_z) #vector dicionario que según el ID guarda posiciones y profundidad

            #dibujamos para UI
            pts_int = pts.astype(int)
            cv2.polylines(frame, [pts_int], True, (0, 255, 0), 2)
            cv2.putText(frame, f"ID:{marker_id} {distance_z:.2f}m",
                    (pts_int[0][0], pts_int[0][1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 1)
            
        #ahora si, posiciones de carro a brazo y de carro a usuario
        #recordando que aruco 25 es carro, 50 es brazo y 10 es usuario 
        dist_carro_brazo = None
        dist_carro_usuario = None

        if 25 in posiciones and 50 in posiciones:
            p_carro, p_brazo = posiciones[25], posiciones[50]
            dist_carro_brazo = abs(p_carro[2] - p_brazo[2]) 
            print(f"Distancia carro-brazo: {dist_carro_brazo:.2f} m")
            
        if 25 in posiciones and 10 in posiciones:
            p_carro, p_usuario = posiciones[25], posiciones[10]
            dist_carro_usuario = abs(p_carro[2] - p_usuario[2])
            print(f"Distancia carro-usuario: {dist_carro_usuario:.2f} m")
    
    #propuesta A: Usamos distancias siempre menores de 25cm para sólo tener que usar dos bits por distancia en hexadecimal,
    #lo que nos permite hasta 255cm con sólo 2 caracteres a mandar por BT
    dist_cb_hex = format(int(dist_carro_brazo*100), '02x') #dist_carro_brazo en cm en hexa
    dist_cu_hex = format(int(dist_carro_usuario*100), '02x') #dist_carro_usuario en cm en hexa
    return dist_cb_hex, dist_cu_hex, frame
#note to self!!! Checar si esta calibración aproximada basta o hay que calibrar con un tablero de ajedrez para obtener coords 3D

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
roi            = None
color_detectado = "NONE"
destino_navegacion = None

while True:

    ret, frame = cap.read()
    # Señales BT -------------------------------------------------------------
    # Leer cámara (siempre, para mantener el buffer fresco)
    if ret and frame is not None:
        color_detectado, roi = detectar_color(frame)
    else:
        time.sleep(0.05)
        continue

    while not bt_queue.empty():
        señal = bt_queue.get()
        print(f"Señal recibida: '{señal}' | Estado: {estado}")

        #FRIENDLY REMINDER: acomodar es cuando el robot acomoda un paquete que le trae el carrito, 
        #recibir es cuando el usuario pide un paquete que ya está acomodado, entonces el robot lo recibe
        # para que el carrito se lo lleve

        if señal == "RL" and estado == IDLE: #RL es para acomodar, RE es para recibir
            modo_actual = "ACOMODAR"
            estado      = DETECTANDO
            print("[SYS] Modo ACOMODAR →cámara detectando color del paquete")

        elif señal == "RE":
            if estado == IDLE:
                # RE llegó primero, esperamos R1-R6
                modo_actual = "RECIBIR"
                estado      = RECIBIR
                print("Modo RECIBIR activado, esperando R1-R6 del MASTER...")
            elif estado == ESPERANDO_RE:
                print(f"RE recibido, navegando hacia el brazo")
                rutina_valida = verificar_rutina_recibir(posicion_pendiente)
                if rutina_valida is not None:
                    rutina_elegida      = rutina_valida
                    posicion_pendiente  = None
                    destino_navegacion  = "BRAZO"   # ← navega primero
                    estado              = NAVEGANDO
                else:
                    print(f"Casilla {posicion_pendiente} vacía → MN al MASTER")
                    bt_send('M', 'N')
                    posicion_pendiente = None
                    modo_actual        = None
                    estado             = IDLE
            else:
                print(f"RE en estado inesperado: {estado}")

        elif señal in ("R1","R2","R3","R4","R5","R6"):
            numero = int(señal[1])
            print(f"[BT] Posición solicitada: {numero} | Estado: {estado}")
            if estado in (RECIBIR, IDLE, ESPERANDO_RE):
                rutina_valida = verificar_rutina_recibir(numero)
                if rutina_valida is not None:
                    print(f"[SYS] Casilla {numero} ocupada → MS al MASTER")
                    bt_send('M', 'S')
                    posicion_pendiente = numero
                    modo_actual        = "RECIBIR"
                    if estado == RECIBIR:
                        print("[SYS] RE ya estaba → navegando hacia brazo")
                        rutina_elegida     = rutina_valida
                        posicion_pendiente = None
                        destino_navegacion = "BRAZO"
                        estado             = NAVEGANDO
                    else:
                        estado = ESPERANDO_RE
                        print(f"[SYS] Esperando RE del SLAVE para rutina {numero}...")
                else:
                    print(f"[SYS] Casilla {numero} vacía → MN al MASTER")
                    bt_send('M', 'N')
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

            elif señal == "MR" and estado == NAVEGANDO:
                if destino_navegacion == "BRAZO":
                    print("[SYS] Llegada al brazo confirmada → iniciando rutina")
                    estado = RUNNING
                    destino_navegacion = None
                elif destino_navegacion == "USUARIO":
                    print("[SYS] Llegada al usuario confirmada → esperando que el usuario tome el paquete")
                    modo_actual = None
                    destino_navegacion = None
                    rutina_elegida = None
                    color_paquete = None
                    color_detectado = "NONE"
                    estado = IDLE
            else:
                print(f"Señal desconocida/ignorada (buuuu)")

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
            print(f"[Slot libre → rutina {rutina_elegida}")
            destino_navegacion = "BRAZO"
            estado = NAVEGANDO
        else:
            print("Sin espacio → ME al MASTER")
            bt_send('M', 'E')
            color_paquete = None
            modo_actual   = None
            estado        = IDLE
    elif estado == NAVEGANDO:
        cb_hex, cu_hex, frame_con_arucos = distancias_arucos(frame)
        bt_send('B', cb_hex) #mandamos distancia carro-bra
        bt_send('U', cu_hex) #mandamos distancia carro-usuario
        print(f"Navegando → destino: {destino_navegacion}")

    elif estado == RUNNING:
        print(f"[SYS] Iniciando ejecución → rutina {rutina_elegida} | Modo: {modo_actual}")
        ok = ejecutar_rutina_dobot(robot, rutina_elegida)
        if ok:
            if modo_actual == "ACOMODAR":
                bt_send('K', '2')   # brazo tomó el paquete
                bt_send('K', 'B')   # brazo terminó rutina
            elif modo_actual == "RECIBIR":
                bt_send('K', 'B')   # brazo terminó rutin
            destino_navegacion = "USUARIO"
            estado             = NAVEGANDO
            print("Rutina completada, navegando hacia el usuario...")

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

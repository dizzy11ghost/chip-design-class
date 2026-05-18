import cv2
import numpy as np
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
ft1 = 23
ft5 = 24
GPIO.setup(ft1, GPIO.OUT)
GPIO.setup(ft5, GPIO.OUT)

#Cámara  --------------------------------
cap = cv2.VideoCapture(0)
lower_red1 = np.array([0,100,100])
upper_red1 = np.array([10,255,255])
lower_red2 = np.array([170,100,100])
upper_red2 = np.array([180,255,255])

lower_blue = np.array([100,100,100])
upper_blue = np.array([140,255,255])

lower_yellow = np.array([22,93,0])
upper_yellow = np.array([45,255,255])

# Simulación de fotoresistencias (busy=1, free=0)
# Solo ft1 y ft2 son reales; el resto simulados
SIMULAR_FT = True  # Nota cambiar a False cuando tengas el hardware completo
ft_simuladas = {
    "ft1": 0,  # libre
    "ft2": 1,  # ocupado
    "ft3": 0,
    "ft4": 1,
    "ft5": 0,
    "ft6": 0,
}

#Estados (más fácil hacer una máquina de estados para el flujo)
IDLE = "IDLE"
DETECTANDO = "DETECTANDO"
DECIDIENDO = "DECIDIENDO"
RUNNING = "RUNNING"

estado = IDLE
color_paquete = None

frames_threshold = 15 #frames viendo el mismo color para poder comprobar que es el paquete
contador_conf = 0
color_candidato = None

def leer_ft(nombre):
    if SIMULAR_FT:
        return ft_simuladas[nombre]
    return GPIO.input(ft1 if nombre == "ft1" else ft5)

#función bluetooth
def bt_signal(msg):
    print(f"[BT]: {msg}")

def ejecutar_rutina_dobot(numero): 
    #simulando la rutina.. jeje
    print(f"[DOBOT]: ejecutando rutina guardada {numero}")
    time.sleep(2)
    #[insertar aqui rutinaaa]
    print("rutina completada")
    bt_signal("Done")

def detectar_color(frame):
    #devuelve rojo, azul, amarillo o None
    height, width, _= frame.shape
    roi = frame[int(height * 0.5):, :]
    hsv = cv2.cvtColor(roi, cv2.COLOR_)
    
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

def decidir_rutina(color):
    slots = {"ROJO": [("ft1", 1), ("ft4", 4)],
            "AZUL": [("ft2", 2), ("ft5", 5)],
            "AMARILLO": [("ft3", 3), ("ft6", 6)]}
    for ft_nombre, rutina in slots[color]:
        if leer_ft(ft_nombre) == 0:
            return rutina
        return None

#Main loop
print("Sistema iniciado. Esperando señal de bluetooth")
estado = DETECTANDO

while True:
    ret, frame = cap.read()
    if not ret:
        break

    color_detectado, roi, areas = detectar_color(frame)

    if estado == DETECTANDO:
        if color_detectado != "NONE":
            if color_detectado == color_candidato:
                contador_conf += 1 #para sumarle a la confirmación
            else:
                color_candidato = color_detectado
                contador_conf = 1
            if contador_confirmacion >= frames_threshold:
                color_paquete         = color_candidato
                estado                = DECIDIENDO
                contador_confirmacion = 0
                color_candidato       = None
                print(f"[CAM] Color confirmado → {color_paquete}")
        else:
            # Ningún color visible → reinicia
            color_candidato       = None
            contador_confirmacion = 0

    # decidiendo
    elif estado == DECIDIENDO:
        rutina = decidir_rutina(color_paquete)
        if rutina is not None:
            print(f"[SYS] Espacio disponible → rutina {rutina}")
            estado = RUNNING
        else:
            print("[SYS] Sin espacio disponible.")
            bt_signal("No hay espacios disponibles")
            estado = IDLE          # o DETECTANDO si quieres reintentar

    # llamar al brazo y regresar a IDL
    elif estado == RUNNING:
        ejecutar_rutina_dobot(rutina)
        color_paquete = None
        estado        = DETECTANDO     # listo para el siguiente paquete
        print(f"[SYS] Estado → {estado}")

    #user interface
    estado_txt = f"Estado: {estado}"
    color_txt  = f"Color: {color_detectado}  (candidato: {color_candidato} x{contador_confirmacion})"
    cv2.putText(roi, estado_txt, (10, 30),  cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
    cv2.putText(roi, color_txt,  (10, 60),  cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200,200,0),   2)
    cv2.imshow("Deteccion", roi)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
GPIO.cleanup()           
    

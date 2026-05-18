import cv2
import numpy as np
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
ft1 = 23
ft4 = 24
GPIO.setup(ft1, GPIO.OUT)
GPIO.setup(ft4, GPIO.OUT)

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

PINES_FT = {
    "ft1": ft1,
    "ft4": ft4}
# Simulación de fotoresistencias (busy=1, free=0)
ft_simuladas = {
    "ft2": 1,  # ocupado
    "ft3": 0,
    "ft5": 0,
    "ft6": 0,
}

#Estados (más fácil hacer una máquina de estados para el flujo)
IDLE = "IDLE"
DETECTANDO = "DETECTANDO"
DECIDIENDO = "DECIDIENDO"
RUNNING = "RUNNING"

estado = DETECTANDO
color_paquete = None
rutina_elegida = None

frames_threshold = 15 #frames viendo el mismo color para poder comprobar que es el paquete
contador_conf = 0
color_candidato = None

#función bluetooth
def bt_signal(msg):
    print(f"[BT]: {msg}")
    
def leer_ft(nombre):
    if nombre in PINES_FT:
        return GPIO.input(PINES_FT[nombre])
    return ft_simuladas.get(nombre, 1)

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

def decidir_rutina(color):
    slots = {"ROJO": [("ft1", 1), ("ft4", 4)],
            "AZUL": [("ft2", 2), ("ft5", 5)],
            "AMARILLO": [("ft3", 3), ("ft6", 6)]}
    for ft_nombre, numero_rutina in slots[color]:
        valor = leer_ft(ft_nombre)
        print(f"[FT]{ft_nombre} = {valor} ({"libre" if valor == 0 else "ocupado"})")
        if valor == 0:
            return numero_rutina
    return None

#Main loop
print("Sistema iniciado. Esperando señal de bluetooth")

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
            if contador_conf >= frames_threshold:
                color_paquete         = color_candidato
                estado                = DECIDIENDO
                contador_conf = 0
                color_candidato       = None
                print(f"[CAM] Color confirmado → {color_paquete}")
        else:
            # Ningún color visible → reinicia
            color_candidato  = None
            contador_conf = 0

    # decidiendo
    elif estado == DECIDIENDO:
        rutina_elegida = decidir_rutina(color_paquete)
        if rutina_elegida is not None:
            print(f"[SYS] Espacio disponible → rutina {rutina_elegida}")
            estado = RUNNING
        else:
            print("[SYS] Sin espacio disponible.")
            bt_signal("No hay espacios disponibles")
            break          # o DETECTANDO si quieres reintentar

    # llamar al brazo y regresar a IDL
    elif estado == RUNNING:
        ejecutar_rutina_dobot(rutina_elegida)
        rutina_elegida = None
        color_paquete = None
        print ("rutina completada")
        estado        = IDLE     # listo para el siguiente paquete
        break

    #user interface
    estado_txt = f"Estado: {estado}"
    color_txt  = f"Color: {color_detectado}  (candidato: {color_candidato} x{contador_conf })"
    cv2.putText(roi, estado_txt, (10, 30),  cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
    cv2.putText(roi, color_txt,  (10, 60),  cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200,200,0),   2)
    cv2.imshow("Deteccion", roi)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
GPIO.cleanup()           
           
    

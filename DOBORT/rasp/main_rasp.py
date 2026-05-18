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

ultimo_color = None

def leer_ft(nombre):
    """Lee una fotoresistencia real o simulada."""
    if SIMULAR_FT:
        return ft_simuladas[nombre]
    if nombre == "ft1":
        return GPIO.input(ft1)
    elif nombre == "ft2":
        return GPIO.input(ft5)
    else:
        return ft_simuladas[nombre]  # resto aún simuladas


#función bluetooth
def bt_signal(msg):
    print(f"[BT]: {msg}")

def ejecutar_rutina_dobot(numero): 
    #simulando la rutina.. jeje
    print(f"[DOBOT]: ejecutando rutina guardada {numero}")
    bt_signal("Done")

def detectar_area(mask):
    #para encontrar la mayor área del color detectado
    contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    mayor_area = 0
    mejor_contorno = None

    for contorno in contours:
        area = cv2.contourArea(contorno)
        if area > 500 and area > mayor_area:
            mayor_area = area
            mejor_contorno = contorno
    return mejor_contorno, mayor_area

def dibujar_rectangulo(frame, contorno, color, etiqueta):
    if contorno is not None:
        x, y, w, h = cv2.boundingRect(contorno)
        cv2.rectangle(frame, (x,y), (x+w, y+h), color, 2)
        cv2.putText(frame, etiqueta, (x, y -10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

def segun_color(color):
    #Lógica de fotoresistencias y rutinas Dobot según el color detectado.
    if color == "ROJO":
        if leer_ft("ft1") == 0:
            ejecutar_rutina_dobot(1)
        elif leer_ft("ft4") == 0:
            ejecutar_rutina_dobot(4)
        else:
            print("No hay espacio disponible para ROJO")
            bt_signal("No hay espacios disponibles")

    elif color == "AZUL":
        if leer_ft("ft2") == 0:
            ejecutar_rutina_dobot(2)
        elif leer_ft("ft5") == 0:
            ejecutar_rutina_dobot(5)
        else:
            print("No hay espacio disponible para AZUL")
            bt_signal("No hay espacios disponibles")

    elif color == "AMARILLO":
        if leer_ft("ft3") == 0:
            ejecutar_rutina_dobot(3)
        elif leer_ft("ft6") == 0:
            ejecutar_rutina_dobot(6)
        else:
            print("No hay espacio disponible para AMARILLO")
            bt_signal("No hay espacios disponibles")

#Main loop
while True:
    ret, frame = cap.read()
    if not ret:
        break
    #leemos sólo la parte inferior
    height, width, _ = frame.shape
    roi = frame[int(height*0.5):height, 0:width]
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    #máscaras de color
    mask_red = (cv2.inRange(hsv, lower_red1, upper_red1)|cv2.inRange(hsv, lower_red2, upper_red2))
    mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)
    mask_yellow = cv2.inRange(hsv, lower_yellow,upper_yellow)

    #detectar áreas
    contorno_red, area_red = detectar_area(mask_red)
    contorno_blue, area_blue = detectar_area(mask_blue)
    contorno_yellow, area_yellow = detectar_area(mask_yellow)

    #dibujar rectángulos
    dibujar_rectangulo(roi, contorno_red, (0,0,255), "ROJO")
    dibujar_rectangulo(roi, contorno_blue, (255,0,0), "AZUL")
    dibujar_rectangulo(roi, contorno_yellow, (0,255,255), "AMARILLO")

    #ver cuál es el color dominante
    areas = {"ROJO": area_red, "AZUL": area_blue, "AMARILLO": area_yellow}
    color_dominante = max(areas, key=areas.get)

    if areas[color_dominante] < 500:  # mismo threshold que detectar_area
        color_dominante = "NONE"

    # Mostrar en el ROI (que es lo que se muestra)
    cv2.putText(roi, f"Color: {color_dominante}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    # Solo actuar cuando cambia el color detectado
    if color_dominante != ultimo_color and color_dominante != "NONE":
        print(f"[CAM]: Nuevo color detectado → {color_dominante}")
        segun_color(color_dominante)
        ultimo_color = color_dominante  # ✅ Actualizar después de procesar
    elif color_dominante == "NONE":
        ultimo_color = None  # Resetea cuando no hay color

    cv2.imshow("Deteccion", roi)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
GPIO.cleanup()

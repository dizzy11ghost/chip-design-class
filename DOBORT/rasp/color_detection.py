import cv2
import numpy as np 

cap = cv2.VideoCapture(0) 

#rangos de colores para las cajas, rojo, amarillo, azul
lower_red1 = np.array([0, 100, 100])
upper_red1 = np.array ([10, 255, 255]) 

lower_red2 = np.array([170, 100, 100])
upper_red2 = np.array ([180, 255, 255]) 

lower_blue = np.array([100, 100, 100])
upper_blue = np.array ([140, 255, 255])

lower_yellow = np.array([22, 93, 0])
upper_yellow = np.array ([45, 255, 255])

while True:
    ret, frame = cap.read()
    if not ret:
        break #si no puede leer un frame para todo

    # Convertir la imagen a HSV
    frame_HSV = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    #máscaras de color
    mask_red = cv2.inRange(frame_HSV, lower_red1, upper_red1) | cv2.inRange(frame_HSV, lower_red2, upper_red2)
    mask_blue = cv2.inRange(frame_HSV, lower_blue, upper_blue)
    mask_yellow = cv2.inRange(frame_HSV, lower_yellow, upper_yellow)

    #contornos en la máscara
    contours_red, _ = cv2.findContours(mask_red, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours_blue, _ = cv2.findContours(mask_blue, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours_yellow, _ = cv2.findContours(mask_yellow, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    #para los rectángulos
    for contour in contours_red:
        area = cv2.contourArea(contour)
        if area  > 500:
            x, y, w, h = cv2.boundingRect(contour)
            cv2.rectangle(frame, (x,y), (x+w, y+h), (0, 0, 255), 2)
            cv2.putText(frame, "ROJO", (x, y -10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    for contour in contours_blue:
        area = cv2.contourArea(contour)
        if area  > 500:
            x, y, w, h = cv2.boundingRect(contour)
            cv2.rectangle(frame, (x,y), (x+w, y+h), (255, 0, 0), 2)
            cv2.putText(frame, "AZUL", (x, y -10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

    for contour in contours_yellow:
        area = cv2.contourArea(contour)
        if area  > 500:
            x, y, w, h = cv2.boundingRect(contour)
            cv2.rectangle(frame, (x,y), (x+w, y+h), (0, 255, 255), 2)
            cv2.putText(frame, "AMARILLO", (x, y -10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

    cv2.imshow("Deteccion colores", frame)
    cv2.waitKey(1)

cap.release()
cv2.destroyAllWindows()

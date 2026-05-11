import cv2
import numpy as np 

cap = cv2.VideoCapture(0) 

lower_fire = np.array([10, 100, 100])
upper_fire = np.array ([25, 255, 255])

while True:
    ret, frame = cap.read()
    if not ret:
        break #si no puede leer un frame para todo

    # Convertir la imagen a HSV
    frame_HSV = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    #máscara para el fuego
    mask = cv2.inRange(frame_HSV, lower_fire, upper_fire)

    #contornos en la máscara
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    #para los rectángulos
    for contour in contours:
        area = cv2.contourArea(contour)
        if area  > 500:
            x, y, w, h = cv2.boundingRect(contour)
            cv2.rectangle(frame, (x,y), (x+w, y+h), (0, 0, 255), 2)
            cv2.putText(frame, "FUEGO", (x, y -10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    cv2.imshow("Deteccion fuego", frame)
    cv2.waitKey(1)

cap.release()
cv2.destroyAllWindows()

import serial
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation

PORT = 'COM5' #puerto
BAUD = 9600 #baudios

ser = serial.Serial(PORT, BAUD, timeout=1)

fig = plt.figure(figsize=(8, 8))
ax = fig.add_subplot(111, projection='polar')
ax.set_theta_zero_location("N") # 0° arriba
ax.set_theta_direction(-1) # Sentido horario
ax.set_ylim(0, 25) # Distancia máxima
ax.grid(True)
ax.set_title("Radar Ultrasónico KL25", pad=20)

angles = []
distances = []

#actualizamos los datos  ------------------------------------------
def update(frame):
    global angles
    global distances

    while ser.in_waiting:
        try:
            #leemos UART -------------------------------
            line = ser.readline().decode('utf-8').strip()
            if not line:
                return

            # Hola para debug
            if "HOLA" in line:
                return

            parts = line.split(',')
            if len(parts) != 2:
                return
            angle = int(parts[0])
            
            distance = float(parts[1]) #recibimos el float de la KL
            # Ignorar timeout
            if distance < 0:
                return

            angle_rad = np.radians(angle) #radianes

            #limpiamos antes de iniciar un nuevo barrido

            if angle <= 1:
                angles.clear()
                distances.clear()

            angles.append(angle_rad) #almacenamiento de ángulos
            distances.append(distance) #almacenamiento de distancia

            ax.clear()
            ax.set_theta_zero_location("N")
            ax.set_theta_direction(-1)
            ax.set_ylim(0, 25)
            ax.grid(True)
            ax.set_title("Radar Ultrasónico KL25", pad=20)

            # Puntos detectados
            ax.scatter(angles, distances, s=20)

            # Línea del barrido actual
            ax.plot([angle_rad, angle_rad], [0, 25])

        except:
            pass

ani = FuncAnimation(fig, update, interval=5)
plt.show()
ser.close() #cerramos la comunicación serial

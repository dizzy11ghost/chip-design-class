# 1ro Instalar: pip install pyserial matplotlib numpy
import serial
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation

# --- CONFIGURACIÓN ---
PORT = 'COM3'  # Confirmar que el puerto este conectado aqui o cambiarlo
BAUD = 9600
ser = serial.Serial(PORT, BAUD, timeout=1) 

# Configuración de la figura Radar
fig = plt.figure(figsize=(6,6))
ax = fig.add_subplot(111, projection='polar')
ax.set_theta_zero_location("N") # 0 grados arriba
ax.set_theta_direction(-1)     # Sentido horario
ax.set_ylim(0, 100)            # Ajusta esto al alcance máximo de tu sensor

# Almacenar los datos
angles = []
distances = []

def update(frame):
    if ser.in_waiting > 0:
        try:
            # Leer línea: "angulo,distancia"
            line = ser.readline().decode('utf-8').strip()
            if not line: return # Si hay timeout o línea vacía, salimos
            
            # Procesar datos
            parts = line.split(',')
            if len(parts) == 2:
                angle = int(parts[0])
                dist = int(parts[1])
                
                # Convertir ángulo a radianes para matplotlib
                angle_rad = np.radians(angle)
                
                # Para un efecto de "barrido", guardamos datos
                # Si el ángulo es 0, limpiamos la lista para reiniciar el ciclo
                if angle == 0:
                    angles.clear()
                    distances.clear()
                
                angles.append(angle_rad)
                distances.append(dist)
                
                # Dibujar
                ax.clear()
                ax.set_theta_zero_location("N")
                ax.set_theta_direction(-1)
                ax.set_ylim(0, 100) # Rango máximo de detección
                ax.scatter(angles, distances, c='red', s=10)
        
        except (ValueError, IndexError): # Ignora líneas corruptas 

# Iniciar animación
ani = FuncAnimation(fig, update, interval=10) # Refresco rápido
plt.show()

# Cerrar puerto al cerrar la ventana
ser.close()

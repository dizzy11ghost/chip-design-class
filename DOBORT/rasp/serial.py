import serial
import threading

# Ajusta el puerto: /dev/rfcomm0 si es BT clásico
ser = serial.Serial('/dev/rfcomm0', 9600, timeout=0.1)

def receive_loop():
    """Hilo que escucha tramas entrantes del Slave."""
    while True:
        dest = ser.read(1)
        if not dest:
            continue
        dato = ser.read(1)
        if not dato:
            continue

        dest = dest.decode('ascii', errors='ignore')
        dato = dato.decode('ascii', errors='ignore')

        if dest == 'R' and dato == 'H':
            # Caso 2: Master → Raspberry vía Slave
            print("Master hola")

# Iniciar hilo de recepción
t = threading.Thread(target=receive_loop, daemon=True)
t.start()

# Caso 3: Raspberry → Slave, LED azul
input("Enter para enviar LED azul al Slave...\n")
ser.write(b'SB')

# Caso 4: Raspberry → Master (pasa por el Slave), LED rojo
input("Enter para enviar LED rojo al Master...\n")
ser.write(b'MR')

print("Escuchando... (Ctrl+C para salir)")
try:
    threading.Event().wait()
except KeyboardInterrupt:
    ser.close()

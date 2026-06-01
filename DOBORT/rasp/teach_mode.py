"""
============================================================
  Dobot Magician - Control via UART con pydobotplus
  Hardware: Raspberry Pi 3 + Dobot Magician (puerto serial)
  IDE:      Geany
  Lib:      pip install pydobotplus
============================================================

ANTES DE CORRER ESTE SCRIPT:
------------------------------
1. Habilitar UART en la RPi 3:
   - Abre terminal y corre: sudo raspi-config
   - Ve a: Interface Options > Serial Port
   - "Would you like a login shell...?" → NO
   - "Would you like the serial port hardware...?" → YES
   - Reinicia la RPi: sudo reboot

2. Agregar tu usuario al grupo dialout (para acceder al puerto):
   sudo usermod -a -G dialout $USER
   (cerrar sesión y volver a entrar para que aplique)

3. Instalar la librería:
   pip install pydobotplus

4. Identificar el puerto correcto:
   ls /dev/tty*
   Normalmente en RPi 3 con UART físico es:
     /dev/ttyS0     ← UART mini (pines GPIO 14/15)
     /dev/ttyAMA0   ← UART completo (puede estar ocupado por Bluetooth)
   Si usas adaptador USB-Serial:
     /dev/ttyUSB0

PINES UART en Raspberry Pi 3 (para conectar al Dobot):
   RPi GPIO 14 (TXD) → Dobot RX
   RPi GPIO 15 (RXD) → Dobot TX
   RPi GND           → Dobot GND
   (NO conectes 5V/3.3V de la RPi al Dobot, el Dobot tiene su propia alimentación)
"""

import time
from pydobotplus import Dobot

# ============================================================
# CONFIGURACIÓN - Cambia esto según tu setup
# ============================================================
PUERTO_SERIAL = "/dev/ttyS0"   # Cambia a /dev/ttyAMA0 o /dev/ttyUSB0 si es necesario
VELOCIDAD     = 100            # mm/s - velocidad de movimiento
ACELERACION   = 100            # mm/s² - aceleración


def inicializar_dobot(puerto):
    """Inicializa la conexión con el Dobot Magician."""
    print(f"[INFO] Conectando al Dobot en {puerto}...")
    try:
        robot = Dobot(port=puerto)
        print("[OK] ¡Dobot conectado exitosamente!")
        return robot
    except Exception as e:
        print(f"[ERROR] No se pudo conectar al Dobot: {e}")
        print("[TIP]  Verifica el puerto serial y que el Dobot esté encendido.")
        raise


def mostrar_posicion(robot):
    """Imprime la posición y ángulos actuales del Dobot."""
    pose = robot.get_pose()
    print("\n--- Posición actual ---")
    print(f"  X: {pose.position.x:.2f} mm")
    print(f"  Y: {pose.position.y:.2f} mm")
    print(f"  Z: {pose.position.z:.2f} mm")
    print(f"  R: {pose.position.r:.2f}°")
    print(f"  Joints: J1={pose.joints.j1:.2f}° | J2={pose.joints.j2:.2f}° | J3={pose.joints.j3:.2f}° | J4={pose.joints.j4:.2f}°")
    print("-----------------------\n")
    return pose


def demo_movimientos(robot):
    """
    Secuencia de movimientos de demostración.
    Ajusta las coordenadas X/Y/Z según el espacio de trabajo de tu Dobot.

    Espacio de trabajo típico del Dobot Magician:
      X: 100 mm a 320 mm (frente al robot)
      Y: -260 mm a 260 mm (lateral)
      Z: -60 mm a 150 mm (altura)
    """

    print("[INFO] Configurando velocidad y aceleración...")
    robot.speed(velocity=VELOCIDAD, acceleration=ACELERACION)

    # ----- POSICIÓN HOME (segura para comenzar) -----
    print("[MOVE] Yendo a posición HOME...")
    robot.move_to(x=220, y=0, z=100, r=0, wait=True)
    mostrar_posicion(robot)
    time.sleep(1)

    # ----- MOVIMIENTO 1: Ir a un punto adelante -----
    print("[MOVE] Movimiento 1 → Punto A (adelante-izquierda, bajo)...")
    robot.move_to(x=200, y=80, z=50, r=0, wait=True)
    mostrar_posicion(robot)
    time.sleep(1)

    # ----- MOVIMIENTO 2: Ir a otro punto -----
    print("[MOVE] Movimiento 2 → Punto B (adelante-derecha, bajo)...")
    robot.move_to(x=200, y=-80, z=50, r=0, wait=True)
    mostrar_posicion(robot)
    time.sleep(1)

    # ----- MOVIMIENTO 3: Subir -----
    print("[MOVE] Movimiento 3 → Subiendo Z...")
    robot.move_to(x=200, y=0, z=120, r=0, wait=True)
    mostrar_posicion(robot)
    time.sleep(1)

    # ----- MOVIMIENTO RELATIVO: Desplazarse +30mm en X -----
    print("[MOVE] Movimiento relativo → +30mm en X...")
    robot.move_rel(x=30, y=0, z=0, r=0, wait=True)
    mostrar_posicion(robot)
    time.sleep(1)

    # ----- DEMO SUCCIÓN (descomenta si tienes ventosa) -----
    # print("[TOOL] Activando succión...")
    # robot.suck(True)
    # time.sleep(2)
    # robot.move_to(x=220, y=0, z=80, r=0, wait=True)
    # time.sleep(1)
    # print("[TOOL] Desactivando succión...")
    # robot.suck(False)

    # ----- REGRESAR A HOME -----
    print("[MOVE] Regresando a HOME...")
    robot.move_to(x=220, y=0, z=100, r=0, wait=True)
    print("[OK] Secuencia completada.\n")


def main():
    robot = None
    try:
        # Inicializar conexión
        robot = inicializar_dobot(PUERTO_SERIAL)

        # Verificar alarmas al inicio
        alarmas = robot.get_alarms()
        if alarmas:
            print(f"[ALERTA] Alarmas activas: {alarmas}")
            print("[INFO]  Limpiando alarmas...")
            robot.clear_alarms()
        else:
            print("[OK] Sin alarmas activas.")

        # Mostrar posición inicial
        print("\n[INFO] Posición inicial:")
        mostrar_posicion(robot)

        # Ejecutar demo de movimientos
        demo_movimientos(robot)

    except KeyboardInterrupt:
        print("\n[INFO] Script interrumpido por el usuario.")

    except Exception as e:
        print(f"[ERROR] {e}")

    finally:
        if robot:
            print("[INFO] Cerrando conexión con el Dobot...")
            robot.close()
            print("[OK] Conexión cerrada.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Control del Dobot Magician desde Raspberry Pi 3
usando UART (GPIO 14/15) y la librería pydobot
"""

import time
import pydobot

# Puerto UART de la Raspberry Pi
PORT = "/dev/ttyS0"

def main():
    print("Conectando al Dobot Magician...")
    
    # Crear instancia del robot
    # verbose=True imprime en consola cada comando enviado (útil para debug)
    robot = pydobot.Dobot(port=PORT, verbose=False)
    
    print("¡Conectado!")

    # --- Leer posición actual ---
    (x, y, z, r, j1, j2, j3, j4) = robot.pose()
    print(f"Posición actual → x:{x:.1f} y:{y:.1f} z:{z:.1f} r:{r:.1f}")
    print(f"Ángulos joints → j1:{j1:.1f} j2:{j2:.1f} j3:{j3:.1f} j4:{j4:.1f}")

    # --- Ajustar velocidad y aceleración ---
    # velocidad: 0-100, aceleración: 0-100
    robot.speed(velocity=50, acceleration=50)

    # --- Movimientos de ejemplo ---

    print("\n▶ Movimiento 1: ir a posición HOME")
    robot.move_to(200, 0, 50, 0, wait=True)
    time.sleep(0.5)

    print("▶ Movimiento 2: mover en X +50mm")
    robot.move_to(250, 0, 50, 0, wait=True)
    time.sleep(0.5)

    print("▶ Movimiento 3: mover en Y +50mm")
    robot.move_to(250, 50, 50, 0, wait=True)
    time.sleep(0.5)

    print("▶ Movimiento 4: bajar en Z -30mm")
    robot.move_to(250, 50, 20, 0, wait=True)
    time.sleep(0.5)

    print("▶ Regresando a posición inicial...")
    robot.move_to(x, y, z, r, wait=True)

    # --- Cerrar conexión ---
    robot.close()
    print("\n✅ Movimientos completados. Conexión cerrada.")

if __name__ == "__main__":
    main()

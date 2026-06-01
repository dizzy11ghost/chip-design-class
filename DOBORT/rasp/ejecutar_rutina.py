"""
============================================================
  Dobot Magician - Ejecutor de Rutinas
  Hardware: Raspberry Pi 3 + Dobot Magician (UART)
  Lib:      pip install pydobotplus
============================================================

Modos de movimiento disponibles:
  MOVJ  → Joint movement. Cada motor va de su ángulo actual
          al ángulo destino independientemente. NO es lineal.
          ✅ Recomendado: muy difícil que se atasque.

  MOVL  → Lineal. El efector sigue una línea recta en el espacio.
          ⚠️  Puede atascarse en singularidades aunque el punto
          sea alcanzable manualmente.

  JUMP  → Sube Z, se mueve en MOVJ, baja Z.
          ✅ Ideal para pick & place (evita colisiones laterales).
"""

import time
import json
import os
from pydobotplus import Dobot

# ============================================================
# CONFIGURACIÓN
# ============================================================
PUERTO_SERIAL   = "/dev/ttyS0"
CARPETA_RUTINAS = "rutinas"
TOTAL_RUTINAS   = 12
VELOCIDAD       = 100    # mm/s
ACELERACION     = 100    # mm/s²

# Modos disponibles en pydobotplus
MODOS = {
    "1": ("MOVJ  — Joint (recomendado, no se atasca)", 0x01),
    "2": ("MOVL  — Lineal (recto, puede atascarse)",   0x02),
    "3": ("JUMP  — Sube/mueve/baja (pick & place)",    0x00),
}


# ============================================================
# UTILIDADES
# ============================================================

def conectar_dobot():
    print(f"[INFO] Conectando al Dobot en {PUERTO_SERIAL}...")
    try:
        robot = Dobot(port=PUERTO_SERIAL)
        print("[OK] ¡Dobot conectado!\n")
        return robot
    except Exception as e:
        print(f"[ERROR] No se pudo conectar: {e}")
        raise


def cargar_rutina(numero):
    """Carga una rutina desde su .json. Retorna None si no existe o está vacía."""
    ruta = os.path.join(CARPETA_RUTINAS, f"rutina_{numero:02d}.json")
    if not os.path.exists(ruta):
        return None, None
    with open(ruta, "r") as f:
        data = json.load(f)
    puntos = data.get("rutina", [])
    nombre = data.get("nombre", f"Rutina {numero:02d}")
    if not puntos:
        return nombre, None
    return nombre, puntos


# ============================================================
# MENÚ PRINCIPAL
# ============================================================

def imprimir_menu_principal():
    os.system("clear")
    print("=" * 55)
    print("   DOBOT MAGICIAN - EJECUTOR DE RUTINAS")
    print("=" * 55)
    print(f"  {'#':<5} {'Nombre':<25} {'Puntos':>7}")
    print("  " + "─" * 40)

    for i in range(1, TOTAL_RUTINAS + 1):
        nombre, puntos = cargar_rutina(i)
        if nombre and puntos:
            print(f"  {i:<5} {nombre:<25} {len(puntos):>7}")
        elif nombre:
            print(f"  {i:<5} {nombre:<25} {'vacía':>7}")
        else:
            print(f"  {i:<5} {'(sin guardar)':<25} {'─':>7}")

    print("  " + "─" * 40)
    print("  [0] Salir")
    print("=" * 55)


def elegir_modo():
    """Muestra las opciones de modo de movimiento y retorna el elegido."""
    print("\n  Modo de movimiento:")
    for key, (desc, _) in MODOS.items():
        print(f"  [{key}] {desc}")
    print()

    while True:
        entrada = input("  Elige modo (1/2/3) [ENTER = MOVJ por defecto]: ").strip()
        if entrada == "" or entrada == "1":
            return MODOS["1"][1], "MOVJ"
        elif entrada in MODOS:
            return MODOS[entrada][1], entrada
        else:
            print("  [!] Opción no válida.")


# ============================================================
# EJECUTOR DE RUTINA
# ============================================================

def ejecutar_rutina(robot, numero):
    nombre, puntos = cargar_rutina(numero)

    if not puntos:
        print(f"\n  [!] La rutina {numero:02d} está vacía o no existe.")
        time.sleep(1.5)
        return

    os.system("clear")
    print("=" * 55)
    print(f"   EJECUTANDO → Rutina {numero:02d}: {nombre}")
    print("=" * 55)
    print(f"  Total de puntos: {len(puntos)}")

    # Mostrar resumen de la rutina
    print(f"\n  {'#':<5} {'X':>8} {'Y':>8} {'Z':>8} {'R':>8} {'Succión':>8}")
    print("  " + "─" * 48)
    for i, p in enumerate(puntos):
        suc = "SÍ" if p.get("succion") else "NO"
        print(f"  {i+1:<5} {p['x']:>8} {p['y']:>8} {p['z']:>8} {p['r']:>8} {suc:>8}")
    print()

    # Elegir modo de movimiento
    modo, modo_nombre = elegir_modo()

    confirmar = input(f"  ¿Ejecutar rutina con modo {modo_nombre}? (s/n): ").strip().lower()
    if confirmar != "s":
        print("  [INFO] Ejecución cancelada.")
        time.sleep(1)
        return

    # Configurar velocidad
    robot.speed(velocity=VELOCIDAD, acceleration=ACELERACION)

    print(f"\n[INFO] Iniciando rutina '{nombre}' en modo {modo_nombre}...\n")

    try:
        for i, punto in enumerate(puntos):
            x   = punto["x"]
            y   = punto["y"]
            z   = punto["z"]
            r   = punto.get("r", 0)
            suc = punto.get("succion", False)

            print(f"  [{i+1}/{len(puntos)}] → X:{x}  Y:{y}  Z:{z}  R:{r}  Succión:{'SÍ' if suc else 'NO'}")

            # Mover al punto con el modo elegido
            robot.move_to(x=x, y=y, z=z, r=r, wait=True, mode=modo)

            # Aplicar succión si corresponde
            robot.suck(suc)

            # Pequeña pausa entre puntos para estabilizar
            time.sleep(0.3)

        print(f"\n[OK] Rutina '{nombre}' completada ({len(puntos)} puntos ejecutados).")

    except KeyboardInterrupt:
        print("\n[INFO] Ejecución interrumpida por el usuario.")
        robot.suck(False)   # Apagar succión por seguridad

    except Exception as e:
        print(f"\n[ERROR] Fallo durante la ejecución: {e}")
        robot.suck(False)

    input("\n  Presiona ENTER para volver al menú...")


# ============================================================
# MAIN
# ============================================================

def main():
    robot = None
    try:
        robot = conectar_dobot()

        alarmas = robot.get_alarms()
        if alarmas:
            print(f"[ALERTA] Alarmas activas: {alarmas}")
            robot.clear_alarms()
            print("[INFO] Alarmas limpiadas.\n")

        while True:
            imprimir_menu_principal()
            entrada = input("\n  Elige una rutina (1-12) o 0 para salir: ").strip()

            if entrada == "0":
                print("\n[INFO] Saliendo.\n")
                break
            elif entrada.isdigit() and 1 <= int(entrada) <= TOTAL_RUTINAS:
                ejecutar_rutina(robot, int(entrada))
            else:
                print("  [!] Opción no válida.")
                time.sleep(1)

    except KeyboardInterrupt:
        print("\n[INFO] Interrumpido por el usuario.")

    except Exception as e:
        print(f"[ERROR] {e}")

    finally:
        if robot:
            robot.suck(False)
            robot.close()
            print("[OK] Conexión cerrada.")


if __name__ == "__main__":
    main()

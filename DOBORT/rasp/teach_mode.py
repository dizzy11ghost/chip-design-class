"""
============================================================
  Dobot Magician - Grabador de Rutinas
  Hardware: Raspberry Pi 3 + Dobot Magician (UART)
  Lib:      pip install pydobotplus
============================================================

Controles:
  ENTER  → guarda la posición actual
  s      → toggle succión (ON/OFF)
  d      → descarta el último punto guardado
  f      → finalizar y guardar rutina en .json
  q      → salir sin guardar
"""

import time
import json
import os
from pydobotplus import Dobot

# ============================================================
# CONFIGURACIÓN
# ============================================================
PUERTO_SERIAL   = "/dev/ttyS0"   # Cambia si es necesario
CARPETA_RUTINAS = "rutinas"      # Carpeta donde se guardan los .json


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


def obtener_posicion(robot):
    """Lee la posición actual del Dobot y la retorna como diccionario."""
    pose = robot.get_pose()
    return {
        "x": round(pose.position.x, 2),
        "y": round(pose.position.y, 2),
        "z": round(pose.position.z, 2),
        "r": round(pose.position.r, 2),
    }


def guardar_json(puntos, nombre_archivo):
    """Guarda la lista de puntos en un archivo .json."""
    os.makedirs(CARPETA_RUTINAS, exist_ok=True)
    if not nombre_archivo.endswith(".json"):
        nombre_archivo += ".json"
    ruta = os.path.join(CARPETA_RUTINAS, nombre_archivo)
    with open(ruta, "w") as f:
        json.dump({"rutina": puntos}, f, indent=4)
    print(f"\n[OK] Rutina guardada en: {ruta}  ({len(puntos)} puntos)")


def imprimir_estado(puntos, succion_activa):
    """Imprime el encabezado con controles y lista de puntos actuales."""
    os.system("clear")
    print("=" * 55)
    print("   GRABADOR DE RUTINAS - Dobot Magician")
    print("=" * 55)
    print("  Controles:")
    print("  ENTER  → guarda la posición actual")
    print("  s      → toggle succión")
    print("  d      → descarta último punto")
    print("  f      → finalizar y guardar")
    print("  q      → salir sin guardar")
    print("─" * 55)

    succion_str = "🟢 ON" if succion_activa else "🔴 OFF"
    print(f"  Succión: {succion_str}    Puntos guardados: {len(puntos)}")
    print("─" * 55)

    if puntos:
        print(f"  {'#':<5} {'X':>8} {'Y':>8} {'Z':>8} {'R':>8} {'Succión':>8}")
        print("  " + "-" * 48)
        for i, p in enumerate(puntos):
            marca = "← último" if i == len(puntos) - 1 else ""
            suc = "SÍ" if p["succion"] else "NO"
            print(f"  {i+1:<5} {p['x']:>8} {p['y']:>8} {p['z']:>8} {p['r']:>8} {suc:>8}  {marca}")
    else:
        print("  (ningún punto guardado todavía)")

    print("─" * 55)


# ============================================================
# LOOP PRINCIPAL
# ============================================================

def grabar(robot):
    puntos        = []
    succion_activa = False

    imprimir_estado(puntos, succion_activa)

    while True:
        entrada = input("  > ").strip().lower()

        # ── ENTER → guardar posición ─────────────────────────
        if entrada == "":
            try:
                pos = obtener_posicion(robot)
                pos["succion"] = succion_activa
                puntos.append(pos)
                suc = "SÍ" if succion_activa else "NO"
                print(f"  [OK] Punto {len(puntos)} guardado → X:{pos['x']}  Y:{pos['y']}  Z:{pos['z']}  Succión:{suc}")
            except Exception as e:
                print(f"  [ERROR] No se pudo leer posición: {e}")
            time.sleep(0.5)
            imprimir_estado(puntos, succion_activa)

        # ── s → toggle succión ───────────────────────────────
        elif entrada == "s":
            succion_activa = not succion_activa
            try:
                robot.suck(succion_activa)
            except Exception as e:
                print(f"  [ERROR] No se pudo cambiar succión: {e}")
            imprimir_estado(puntos, succion_activa)

        # ── d → descartar último punto ───────────────────────
        elif entrada == "d":
            if puntos:
                eliminado = puntos.pop()
                print(f"  [OK] Último punto eliminado → X:{eliminado['x']}  Y:{eliminado['y']}  Z:{eliminado['z']}")
                time.sleep(0.5)
                imprimir_estado(puntos, succion_activa)
            else:
                print("  [!] No hay puntos para descartar.")

        # ── f → finalizar y guardar ──────────────────────────
        elif entrada == "f":
            if not puntos:
                print("  [!] No hay puntos guardados. Agrega al menos uno.")
                continue
            imprimir_estado(puntos, succion_activa)
            nombre = input("  Nombre del archivo (sin .json): ").strip()
            if nombre:
                guardar_json(puntos, nombre)
                break
            else:
                print("  [!] Nombre inválido, no se guardó.")

        # ── q → salir sin guardar ────────────────────────────
        elif entrada == "q":
            if puntos:
                confirmar = input(f"  Tienes {len(puntos)} punto(s) sin guardar. ¿Salir? (s/n): ").strip().lower()
                if confirmar != "s":
                    imprimir_estado(puntos, succion_activa)
                    continue
            print("\n[INFO] Saliendo sin guardar.")
            break

        else:
            print("  [!] Tecla no reconocida. Usa ENTER, s, d, f o q.")


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

        grabar(robot)

    except KeyboardInterrupt:
        print("\n[INFO] Interrumpido por el usuario.")

    except Exception as e:
        print(f"[ERROR] {e}")

    finally:
        if robot:
            robot.close()
            print("[OK] Conexión cerrada.")


if __name__ == "__main__":
    main()

"""
============================================================
  Dobot Magician - Gestor de 12 Rutinas
  Hardware: Raspberry Pi 3 + Dobot Magician (UART)
  Lib:      pip install pydobotplus
============================================================

Flujo:
  1. Se muestra la lista de las 12 rutinas (vacías o con puntos).
  2. Elige una rutina para crear o modificar.
  3. Dentro del editor:
       ENTER  → guarda la posición actual
       s      → toggle succión (ON/OFF)
       d      → descarta el último punto
       f      → finalizar y guardar esta rutina
       q      → salir del editor sin guardar cambios
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


# ============================================================
# PERSISTENCIA
# ============================================================

def ruta_archivo(numero):
    """Retorna la ruta del .json para la rutina dada (1-12)."""
    os.makedirs(CARPETA_RUTINAS, exist_ok=True)
    return os.path.join(CARPETA_RUTINAS, f"rutina_{numero:02d}.json")


def cargar_rutina(numero):
    """Carga una rutina desde su .json. Retorna lista vacía si no existe."""
    ruta = ruta_archivo(numero)
    if os.path.exists(ruta):
        with open(ruta, "r") as f:
            data = json.load(f)
        return data.get("rutina", [])
    return []


def guardar_rutina(numero, puntos, nombre):
    """Guarda la rutina en su .json correspondiente."""
    ruta = ruta_archivo(numero)
    with open(ruta, "w") as f:
        json.dump({"nombre": nombre, "rutina": puntos}, f, indent=4)


def cargar_nombre(numero):
    """Carga el nombre guardado de una rutina, si existe."""
    ruta = ruta_archivo(numero)
    if os.path.exists(ruta):
        with open(ruta, "r") as f:
            data = json.load(f)
        return data.get("nombre", f"Rutina {numero:02d}")
    return None


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
    pose = robot.get_pose()
    return {
        "x": round(pose.position.x, 2),
        "y": round(pose.position.y, 2),
        "z": round(pose.position.z, 2),
        "r": round(pose.position.r, 2),
    }


# ============================================================
# MENÚ PRINCIPAL - Lista de 12 rutinas
# ============================================================

def imprimir_menu_principal():
    os.system("clear")
    print("=" * 55)
    print("   DOBOT MAGICIAN - GESTOR DE RUTINAS")
    print("=" * 55)
    print(f"  {'#':<5} {'Nombre':<25} {'Puntos':>7}")
    print("  " + "─" * 40)

    for i in range(1, TOTAL_RUTINAS + 1):
        nombre = cargar_nombre(i)
        puntos = cargar_rutina(i)
        if nombre:
            print(f"  {i:<5} {nombre:<25} {len(puntos):>7}")
        else:
            print(f"  {i:<5} {'(vacía)':<25} {'─':>7}")

    print("  " + "─" * 40)
    print("  [0] Salir")
    print("=" * 55)


def menu_principal(robot):
    while True:
        imprimir_menu_principal()
        entrada = input("\n  Elige una rutina (1-12) o 0 para salir: ").strip()

        if entrada == "0":
            print("\n[INFO] Saliendo del gestor.\n")
            break

        if entrada.isdigit() and 1 <= int(entrada) <= TOTAL_RUTINAS:
            numero = int(entrada)
            editor_rutina(robot, numero)
        else:
            print("  [!] Opción no válida.")
            time.sleep(1)


# ============================================================
# EDITOR DE RUTINA
# ============================================================

def imprimir_editor(numero, nombre, puntos, succion_activa):
    os.system("clear")
    succion_str = "🟢 ON" if succion_activa else "🔴 OFF"
    print("=" * 55)
    print(f"   EDITANDO → Rutina {numero:02d}: {nombre}")
    print("=" * 55)
    print("  Controles:")
    print("  ENTER  → guarda la posición actual")
    print("  s      → toggle succión")
    print("  d      → descarta último punto")
    print("  f      → finalizar y guardar rutina")
    print("  q      → salir sin guardar cambios")
    print("─" * 55)
    print(f"  Succión: {succion_str}    Puntos guardados: {len(puntos)}")
    print("─" * 55)

    if puntos:
        print(f"  {'#':<5} {'X':>8} {'Y':>8} {'Z':>8} {'R':>8} {'Succión':>8}")
        print("  " + "-" * 48)
        for i, p in enumerate(puntos):
            marca = "← último" if i == len(puntos) - 1 else ""
            suc   = "SÍ" if p.get("succion") else "NO"
            print(f"  {i+1:<5} {p['x']:>8} {p['y']:>8} {p['z']:>8} {p['r']:>8} {suc:>8}  {marca}")
    else:
        print("  (ningún punto guardado todavía)")

    print("─" * 55)


def editor_rutina(robot, numero):
    # Cargar estado previo si existe
    puntos         = cargar_rutina(numero)
    nombre_previo  = cargar_nombre(numero) or f"Rutina {numero:02d}"
    succion_activa = False

    # Pedir nombre (mantener el anterior si ya tenía uno)
    os.system("clear")
    print(f"  Editando Rutina {numero:02d}")
    print(f"  Nombre actual: {nombre_previo}")
    nuevo_nombre = input("  Nuevo nombre (ENTER para mantener el actual): ").strip()
    nombre = nuevo_nombre if nuevo_nombre else nombre_previo

    imprimir_editor(numero, nombre, puntos, succion_activa)

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
            imprimir_editor(numero, nombre, puntos, succion_activa)

        # ── s → toggle succión ───────────────────────────────
        elif entrada == "s":
            succion_activa = not succion_activa
            try:
                robot.suck(succion_activa)
            except Exception as e:
                print(f"  [ERROR] No se pudo cambiar succión: {e}")
            imprimir_editor(numero, nombre, puntos, succion_activa)

        # ── d → descartar último punto ───────────────────────
        elif entrada == "d":
            if puntos:
                eliminado = puntos.pop()
                print(f"  [OK] Último punto eliminado → X:{eliminado['x']}  Y:{eliminado['y']}  Z:{eliminado['z']}")
                time.sleep(0.5)
                imprimir_editor(numero, nombre, puntos, succion_activa)
            else:
                print("  [!] No hay puntos para descartar.")

        # ── f → finalizar y guardar ──────────────────────────
        elif entrada == "f":
            if not puntos:
                print("  [!] No hay puntos guardados. Agrega al menos uno.")
                continue
            guardar_rutina(numero, puntos, nombre)
            print(f"\n  [OK] Rutina {numero:02d} '{nombre}' guardada ({len(puntos)} puntos).")
            time.sleep(1.5)
            break

        # ── q → salir sin guardar ────────────────────────────
        elif entrada == "q":
            confirmar = input("  ¿Salir sin guardar cambios? (s/n): ").strip().lower()
            if confirmar == "s":
                print("  [INFO] Cambios descartados.")
                time.sleep(1)
                break
            imprimir_editor(numero, nombre, puntos, succion_activa)

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

        menu_principal(robot)

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

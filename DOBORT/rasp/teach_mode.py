"""
teach_mode.py
─────────────────────────────────────────────────────────────
Script para grabar rutinas del Dobot Magician.
Compatible con Thonny. Usa pydobotplus.

Controles:
  ENTER  → guarda la posición actual
  s      → toggle succión
  d      → descarta último punto
  f      → finalizar y guardar
  q      → salir sin guardar
─────────────────────────────────────────────────────────────
"""

import json
import os
import sys
import time

from pydobotplus import Dobot

# ── Config ────────────────────────────────────────────────────────────────────
PORT          = '/dev/ttyAMA0'
RUTINAS_FILE  = 'rutinas.json'

SLOT_INFO = {
    1: "ROJO     – ft1",
    2: "AZUL     – ft2",
    3: "AMARILLO – ft3",
    4: "ROJO     – ft4",
    5: "AZUL     – ft5",
    6: "AMARILLO – ft6",
}

# ── JSON helpers ──────────────────────────────────────────────────────────────
def cargar_rutinas():
    if os.path.exists(RUTINAS_FILE):
        try:
            with open(RUTINAS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def guardar_rutinas(rutinas):
    with open(RUTINAS_FILE, 'w', encoding='utf-8') as f:
        json.dump(rutinas, f, indent=2, ensure_ascii=False)
    print(f"\n[TEACH] Guardado en '{RUTINAS_FILE}'")


# ── Display ───────────────────────────────────────────────────────────────────
def fmt_punto(p, idx):
    suc = "SUCCION ON" if p['suction'] else "succion off"
    return (
        f"  [{idx}] "
        f"X={p['x']:7.2f}  "
        f"Y={p['y']:7.2f}  "
        f"Z={p['z']:7.2f}  "
        f"R={p['r']:6.2f}  "
        f"{suc}"
    )


def imprimir_rutina(puntos):
    if not puntos:
        print("   (sin puntos todavía)")
        return
    for i, p in enumerate(puntos):
        print(fmt_punto(p, i))


# ── Lectura de pose con pydobotplus ───────────────────────────────────────────
def leer_pose(robot):
    """
    pydobotplus expone pose() → (x, y, z, r, j1, j2, j3, j4).
    Devuelve (x, y, z, r) o None si falla.
    """
    try:
        pose = robot.pose()
        return pose[0], pose[1], pose[2], pose[3]
    except Exception as e:
        print(f"\n[ERROR] No se pudo leer pose: {e}")
        return None


# ── Toggle succión con pydobotplus ────────────────────────────────────────────
def set_suction(robot, enable: bool):
    """
    pydobotplus usa suction_cup(enable) en lugar de suck().
    """
    try:
        robot.suction_cup(enable)
    except AttributeError:
        # Fallback por si la versión instalada aún usa suck()
        try:
            robot.suck(enable)
        except Exception as e:
            print(f"[ERROR] Succión: {e}")


# ── Grabado de rutina ─────────────────────────────────────────────────────────
def grabar_rutina(robot, num_rutina):
    puntos     = []
    suction_on = False

    print(f"\n{'─'*55}")
    print(f"  GRABANDO RUTINA {num_rutina}")
    print(f"  {SLOT_INFO.get(num_rutina, '?')}")
    print(f"{'─'*55}")
    print("  ENTER -> guardar posición actual")
    print("  s     -> toggle succión")
    print("  d     -> borrar último punto")
    print("  f     -> finalizar y guardar")
    print("  q     -> cancelar")
    print(f"{'─'*55}")

    while True:
        pose = leer_pose(robot)
        if pose is None:
            time.sleep(0.2)
            continue

        x, y, z, r = pose
        suc_tag = "SUC:ON " if suction_on else "suc:off"

        print(
            f"\n{suc_tag} "
            f"X={x:7.2f}  Y={y:7.2f}  Z={z:7.2f}  R={r:6.2f}"
        )

        tecla = input("[ENTER/s/d/f/q] > ").strip().lower()

        # ── Guardar punto ─────────────────────────
        if tecla == '':
            punto = {
                "x":       round(x, 2),
                "y":       round(y, 2),
                "z":       round(z, 2),
                "r":       round(r, 2),
                "suction": suction_on,
            }
            puntos.append(punto)
            print(f"\n[PUNTO] Punto {len(puntos)-1} guardado")
            imprimir_rutina(puntos)

        # ── Toggle succión ────────────────────────
        elif tecla == 's':
            suction_on = not suction_on
            set_suction(robot, suction_on)
            print(f"\n[SUCCION] {'ON' if suction_on else 'OFF'}")

        # ── Borrar último ─────────────────────────
        elif tecla == 'd':
            if puntos:
                eliminado = puntos.pop()
                print("\n[PUNTO] Eliminado:")
                print(fmt_punto(eliminado, len(puntos)))
            else:
                print("\n[PUNTO] No hay puntos que borrar")

        # ── Finalizar ─────────────────────────────
        elif tecla == 'f':
            set_suction(robot, False)
            if not puntos:
                print("\n[TEACH] Rutina vacía — no se guarda")
                return []
            print(f"\n[TEACH] Rutina {num_rutina} con {len(puntos)} puntos lista.")
            return puntos

        # ── Cancelar ──────────────────────────────
        elif tecla == 'q':
            set_suction(robot, False)
            print("\n[TEACH] Cancelado — rutina descartada")
            return []

        else:
            print("\n[INFO] Tecla no reconocida")

        time.sleep(0.05)


# ── Menú principal ────────────────────────────────────────────────────────────
def menu():
    rutinas = cargar_rutinas()

    print("\n+================================================+")
    print("|      DOBOT TEACH MODE  (pydobotplus)          |")
    print("+================================================+")
    print(
        f"  Rutinas guardadas: "
        f"{list(rutinas.keys()) if rutinas else 'ninguna'}\n"
    )

    for num, desc in SLOT_INFO.items():
        marca = "[OK]" if str(num) in rutinas else "[  ]"
        print(f"  [{num}]  {desc:<22}  {marca}")

    print("\n  [7] Ver rutina")
    print("  [8] Borrar rutina")
    print("  [0] Salir\n")

    op = input("Opción: ").strip()

    # ── Grabar rutina (1-6) ──────────────────────
    if op in [str(n) for n in range(1, 7)]:
        num = int(op)

        if str(num) in rutinas:
            r = input(
                f"Rutina {num} ya existe. ¿Sobreescribir? (s/N): "
            ).strip().lower()
            if r != 's':
                return

        print(f"\n[TEACH] Conectando a Dobot en {PORT}…")
        try:
            robot = Dobot(port=PORT, verbose=False)
        except Exception as e:
            print(f"[ERROR] No se pudo conectar: {e}")
            return

        print("[TEACH] Conectado  ✓")
        print("Mueve el brazo manualmente (usa el botón de liberación del Dobot)")

        puntos = grabar_rutina(robot, num)

        try:
            robot.close()
        except Exception:
            pass

        if puntos:
            rutinas[str(num)] = puntos
            guardar_rutinas(rutinas)

    # ── Ver rutina ───────────────────────────────
    elif op == '7':
        n = input("Número de rutina: ").strip()
        if n in rutinas:
            print(f"\nRutina {n}")
            print("─" * 40)
            imprimir_rutina(rutinas[n])
        else:
            print("No existe esa rutina")

    # ── Borrar rutina ────────────────────────────
    elif op == '8':
        n = input("Número de rutina a borrar: ").strip()
        if n in rutinas:
            del rutinas[n]
            guardar_rutinas(rutinas)
            print(f"Rutina {n} borrada")
        else:
            print("No existe esa rutina")

    # ── Salir ────────────────────────────────────
    elif op == '0':
        print("\nSaliendo…")
        sys.exit(0)

    else:
        print("\nOpción inválida")


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    while True:
        try:
            menu()
        except KeyboardInterrupt:
            print("\n\nInterrumpido por usuario")
            sys.exit(0)
        except Exception as e:
            print(f"\n[ERROR GENERAL] {e}")

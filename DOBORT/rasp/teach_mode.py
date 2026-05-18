"""
teach_mode.py
─────────────────────────────────────────────────────────────
Script independiente para grabar rutinas del Dobot Magician.
Compatible con Thonny (sin termios/getch).

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
import pydobot

# ── Config ────────────────────────────────────────────────────────────────────
PORT = '/dev/ttyAMA0'
RUTINAS_FILE = 'rutinas.json'

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
        except:
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

# ── Grabado de rutina ─────────────────────────────────────────────────────────
def grabar_rutina(robot, num_rutina):

    puntos = []
    suction_on = False

    print(f"\n{'─'*55}")
    print(f"  GRABANDO RUTINA {num_rutina}")
    print(f"  {SLOT_INFO.get(num_rutina, '?')}")
    print(f"{'─'*55}")

    print("  ENTER -> guardar posición")
    print("  s     -> toggle succión")
    print("  d     -> borrar último punto")
    print("  f     -> finalizar y guardar")
    print("  q     -> cancelar")
    print(f"{'─'*55}")

    while True:

        try:
            pose = robot.pose()

            x = pose[0]
            y = pose[1]
            z = pose[2]
            r = pose[3]

        except Exception as e:
            print("\n[ERROR] No se pudo leer pose:", e)
            continue

        suc_tag = "SUC:ON " if suction_on else "suc:off"

        print(
            f"\n{suc_tag} "
            f"X={x:7.2f}  "
            f"Y={y:7.2f}  "
            f"Z={z:7.2f}  "
            f"R={r:6.2f}"
        )

        tecla = input("[ENTER/s/d/f/q] > ").strip().lower()

        # ── Guardar punto ─────────────────────────
        if tecla == '':

            punto = {
                "x": round(x, 2),
                "y": round(y, 2),
                "z": round(z, 2),
                "r": round(r, 2),
                "suction": suction_on
            }

            puntos.append(punto)

            print(f"\n[PUNTO] Punto {len(puntos)-1} guardado")
            imprimir_rutina(puntos)

        # ── Toggle succión ────────────────────────
        elif tecla == 's':

            suction_on = not suction_on

            try:
                robot.suck(enable=suction_on)
            except:
                try:
                    robot.suck(suction_on)
                except Exception as e:
                    print("[ERROR] Succión:", e)

            estado = "ON" if suction_on else "OFF"

            print(f"\n[SUCCION] {estado}")

        # ── Borrar último ─────────────────────────
        elif tecla == 'd':

            if puntos:

                eliminado = puntos.pop()

                print("\n[PUNTO] Eliminado:")
                print(fmt_punto(eliminado, len(puntos)))

            else:
                print("\n[PUNTO] No hay puntos")

        # ── Finalizar ─────────────────────────────
        elif tecla == 'f':

            try:
                robot.suck(False)
            except:
                pass

            if not puntos:
                print("\n[TEACH] Rutina vacía")
                return []

            print(
                f"\n[TEACH] Rutina {num_rutina} "
                f"guardada con {len(puntos)} puntos"
            )

            return puntos

        # ── Cancelar ──────────────────────────────
        elif tecla == 'q':

            try:
                robot.suck(False)
            except:
                pass

            print("\n[TEACH] Cancelado")

            return []

        else:
            print("\n[INFO] Comando no válido")

        time.sleep(0.05)

# ── Menú principal ────────────────────────────────────────────────────────────
def menu():

    rutinas = cargar_rutinas()

    print("\n+================================================+")
    print("|      DOBOT TEACH MODE - Grabar rutinas        |")
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

    # ── Grabar rutina ────────────────────────────
    if op in [str(n) for n in range(1, 7)]:

        num = int(op)

        if str(num) in rutinas:

            r = input(
                f"Rutina {num} ya existe. "
                f"Sobreescribir? (s/N): "
            ).strip().lower()

            if r != 's':
                return

        print(f"\n[TEACH] Conectando a Dobot en {PORT}...")

        try:
            robot = pydobot.Dobot(
                port=PORT,
                verbose=False
            )

        except Exception as e:
            print("[ERROR] No se pudo conectar:", e)
            return

        print("[TEACH] Conectado")
        print(
            "Mueve el brazo manualmente "
            "(usa el botón del Dobot para liberar motores)"
        )

        puntos = grabar_rutina(robot, num)

        try:
            robot.close()
        except:
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
            print("No existe")

    # ── Borrar rutina ────────────────────────────
    elif op == '8':

        n = input("Número de rutina a borrar: ").strip()

        if n in rutinas:

            del rutinas[n]

            guardar_rutinas(rutinas)

            print(f"Rutina {n} borrada")

        else:
            print("No existe")

    # ── Salir ────────────────────────────────────
    elif op == '0':

        print("\nSaliendo...")
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
            print("\n[ERROR GENERAL]", e)

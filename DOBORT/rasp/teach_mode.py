"""
teach_mode.py
─────────────────────────────────────────────────────────────
Script independiente para grabar rutinas del Dobot Magician.
Usa pydobot (igual que el script principal) y solo genera
rutinas.json — no toca nada del sistema principal.

Controles en terminal:
  ENTER  → guarda la posición actual como siguiente punto
  s      → toggle succión (ON/OFF en hardware y en el punto)
  d      → descarta el último punto guardado
  f      → finaliza y guarda la rutina en rutinas.json
  q      → salir sin guardar
─────────────────────────────────────────────────────────────
"""

import json
import os
import sys
import tty
import termios
import pydobot

# ── Config ────────────────────────────────────────────────────────────────────
PORT         = '/dev/ttyAMA0'
RUTINAS_FILE = 'rutinas.json'

SLOT_INFO = {
    1: "ROJO     – ft1",
    2: "AZUL     – ft2",
    3: "AMARILLO – ft3",
    4: "ROJO     – ft4",
    5: "AZUL     – ft5",
    6: "AMARILLO – ft6",
}

# ── Lectura de tecla sin Enter ────────────────────────────────────────────────
def getch() -> str:
    fd  = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    return ch

# ── JSON helpers ──────────────────────────────────────────────────────────────
def cargar_rutinas() -> dict:
    if os.path.exists(RUTINAS_FILE):
        with open(RUTINAS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def guardar_rutinas(rutinas: dict):
    with open(RUTINAS_FILE, 'w', encoding='utf-8') as f:
        json.dump(rutinas, f, indent=2, ensure_ascii=False)
    print(f"\n[TEACH] Guardado en '{RUTINAS_FILE}'")

# ── Display ───────────────────────────────────────────────────────────────────
def fmt_punto(p: dict, idx: int) -> str:
    suc = "SUCCION ON" if p['suction'] else "succion off"
    return f"  [{idx}] X={p['x']:7.2f}  Y={p['y']:7.2f}  Z={p['z']:7.2f}  R={p['r']:6.2f}  {suc}"

def imprimir_rutina(puntos: list):
    if not puntos:
        print("   (sin puntos todavia)")
        return
    for i, p in enumerate(puntos):
        print(fmt_punto(p, i))

# ── Grabado de una rutina ─────────────────────────────────────────────────────
def grabar_rutina(robot: pydobot.Dobot, num_rutina: int) -> list:
    puntos: list[dict] = []
    suction_on = False

    print(f"\n{'─'*52}")
    print(f"  GRABANDO RUTINA {num_rutina}  ({SLOT_INFO.get(num_rutina, '?')})")
    print(f"{'─'*52}")
    print("  ENTER -> guardar posicion actual")
    print("  s     -> toggle succion")
    print("  d     -> descartar ultimo punto")
    print("  f     -> finalizar y guardar")
    print("  q     -> cancelar sin guardar")
    print(f"{'─'*52}\n")

    while True:
        (x, y, z, r, *_) = robot.pose()

        suc_tag = "SUC:ON " if suction_on else "suc:off"
        sys.stdout.write(
            f"\r  {suc_tag}  X={x:7.2f}  Y={y:7.2f}  Z={z:7.2f}  R={r:6.2f}"
            "  | ENTER/s/d/f/q > "
        )
        sys.stdout.flush()

        tecla = getch()

        if tecla in ('\r', '\n'):           # ENTER — guardar punto
            punto = {
                "x":       round(x, 2),
                "y":       round(y, 2),
                "z":       round(z, 2),
                "r":       round(r, 2),
                "suction": suction_on,
            }
            puntos.append(punto)
            print(f"\n  Punto {len(puntos)-1} guardado")
            imprimir_rutina(puntos)

        elif tecla == 's':                  # toggle succion
            suction_on = not suction_on
            robot.suck(suction_on)
            estado = "ON" if suction_on else "OFF"
            print(f"\n  Succion -> {estado}")

        elif tecla == 'd':                  # descartar ultimo
            if puntos:
                p = puntos.pop()
                print(f"\n  Descartado: {fmt_punto(p, len(puntos))}")
            else:
                print("\n  (no hay puntos)")

        elif tecla == 'f':                  # finalizar
            if suction_on:
                robot.suck(False)
            if not puntos:
                print("\n  [TEACH] Rutina vacia, no se guarda.")
                return []
            print(f"\n  Rutina {num_rutina} lista — {len(puntos)} punto(s).")
            return puntos

        elif tecla == 'q':                  # cancelar
            if suction_on:
                robot.suck(False)
            print("\n  [TEACH] Cancelado.")
            return []

# ── Menu ──────────────────────────────────────────────────────────────────────
def menu():
    rutinas = cargar_rutinas()

    print("\n+================================================+")
    print("|      DOBOT TEACH MODE  -  Grabar rutinas      |")
    print("+================================================+")
    print(f"  Rutinas guardadas: {list(rutinas.keys()) or 'ninguna'}\n")

    for num, desc in SLOT_INFO.items():
        marca = "[OK]" if str(num) in rutinas else "[  ]"
        print(f"  [{num}]  {desc:<22}  {marca}")

    print("\n  [7]  Ver puntos de una rutina")
    print("  [8]  Borrar una rutina")
    print("  [0]  Salir\n")

    op = input("  Opcion: ").strip()

    if op in [str(n) for n in range(1, 7)]:
        num = int(op)
        if str(num) in rutinas:
            r = input(f"  Rutina {num} ya existe. Sobreescribir? (s/N): ").strip().lower()
            if r != 's':
                return

        print(f"\n[TEACH] Conectando al Dobot en {PORT}...")
        robot = pydobot.Dobot(port=PORT, verbose=False)
        print("[TEACH] Conectado. Mueve el brazo a mano (presiona boton para liberar motores).\n")

        puntos = grabar_rutina(robot, num)
        robot.close()

        if puntos:
            rutinas[str(num)] = puntos
            guardar_rutinas(rutinas)

    elif op == '7':
        n = input("  Numero de rutina: ").strip()
        if n in rutinas:
            print(f"\n  Rutina {n}:")
            imprimir_rutina(rutinas[n])
        else:
            print("  No existe.")

    elif op == '8':
        n = input("  Numero de rutina a borrar: ").strip()
        if n in rutinas:
            del rutinas[n]
            guardar_rutinas(rutinas)
            print(f"  Rutina {n} borrada.")
        else:
            print("  No existe.")

    elif op == '0':
        sys.exit(0)

# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == '__main__':
    while True:
        menu()
        print()

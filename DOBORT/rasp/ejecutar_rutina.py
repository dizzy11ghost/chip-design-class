"""
ejecutar_rutina.py
────────────────────────────────────────────
Ejecuta rutinas guardadas del Dobot
────────────────────────────────────────────
"""

import json
import time
import pydobot

PORT = "/dev/ttyAMA0"
RUTINAS_FILE = "rutinas.json"

# ── Leer JSON ─────────────────────────────
try:
    with open(RUTINAS_FILE, "r", encoding="utf-8") as f:
        rutinas = json.load(f)

except Exception as e:
    print("[ERROR] No se pudo leer rutinas.json")
    print(e)
    exit()

# ── Mostrar rutinas ───────────────────────
print("\nRutinas disponibles:\n")

for nombre in rutinas.keys():
    print(f"  [{nombre}]")

rutina_num = input("\nNúmero de rutina a ejecutar: ").strip()

if rutina_num not in rutinas:
    print("Rutina no encontrada")
    exit()

puntos = rutinas[rutina_num]

print(f"\nConectando al Dobot en {PORT}...")

# ── Conectar Dobot ────────────────────────
try:
    robot = pydobot.Dobot(
        port=PORT,
        verbose=False
    )

except Exception as e:
    print("[ERROR] No se pudo conectar")
    print(e)
    exit()

print("Conectado")

# ── Ejecutar puntos ───────────────────────
for i, p in enumerate(puntos):

    print(f"\nMoviendo a punto {i}")

    x = p["x"]
    y = p["y"]
    z = p["z"]
    r = p["r"]

    suction = p["suction"]

    print(
        f"X={x} "
        f"Y={y} "
        f"Z={z} "
        f"R={r} "
        f"SUC={suction}"
    )

    # Movimiento
    robot.move_to(
        x,
        y,
        z,
        r,
        wait=True
    )

    # Succión
    try:
        robot.suck(enable=suction)
    except:
        robot.suck(suction)

    time.sleep(0.5)

# ── Apagar succión al final ───────────────
try:
    robot.suck(False)
except:
    pass

robot.close()

print("\nRutina terminada")

"""
ejecutar_rutina.py
─────────────────────────────────────────────────────────────
Ejecuta rutinas grabadas con teach_mode.py en el Dobot Magician.
Usa pydobotplus. Al terminar, desconecta el robot.

Uso:
  python ejecutar_rutina.py
─────────────────────────────────────────────────────────────
"""

import json
import math
import os
import sys
import time

from pydobotplus import Dobot

# ── Config ────────────────────────────────────────────────────────────────────
PORT         = '/dev/ttyAMA0'
RUTINAS_FILE = 'rutinas.json'

# Punto seguro de tránsito — ajusta según tu setup
SAFE_POINT = {"x": 200.0, "y": 0.0, "z": 80.0, "r": 0.0}

# Workspace válido del Dobot Magician
WS_RADIO_MIN = 130.0
WS_RADIO_MAX = 320.0
WS_Z_MIN     = -70.0
WS_Z_MAX     = 150.0

# Velocidad y aceleración (0-100). Baja estos valores si hay alarmas.
VELOCIDAD    = 40
ACELERACION  = 30

ALARM_CLEAR_WAIT = 1.5  # s tras limpiar alarma

SLOT_INFO = {
    "1": "ROJO     – ft1",
    "2": "AZUL     – ft2",
    "3": "AMARILLO – ft3",
    "4": "ROJO     – ft4",
    "5": "AZUL     – ft5",
    "6": "AMARILLO – ft6",
}

# ── JSON ──────────────────────────────────────────────────────────────────────
def cargar_rutinas():
    if not os.path.exists(RUTINAS_FILE):
        print(f"[ERROR] No se encontró '{RUTINAS_FILE}'")
        print("        Graba rutinas primero con teach_mode.py")
        sys.exit(1)
    try:
        with open(RUTINAS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] No se pudo leer '{RUTINAS_FILE}': {e}")
        sys.exit(1)

# ── Validación workspace ──────────────────────────────────────────────────────
def punto_alcanzable(x, y, z):
    radio = math.sqrt(x**2 + y**2)
    if radio < WS_RADIO_MIN:
        return False, f"radio {radio:.1f} mm < mínimo {WS_RADIO_MIN} mm (zona muerta)"
    if radio > WS_RADIO_MAX:
        return False, f"radio {radio:.1f} mm > máximo {WS_RADIO_MAX} mm"
    if z < WS_Z_MIN:
        return False, f"Z={z} mm < límite inferior {WS_Z_MIN} mm"
    if z > WS_Z_MAX:
        return False, f"Z={z} mm > límite superior {WS_Z_MAX} mm"
    return True, ""

# ── Succión ───────────────────────────────────────────────────────────────────
def set_suction(robot, enable: bool):
    try:
        robot.suction_cup(enable)
    except AttributeError:
        try:
            robot.suck(enable)
        except Exception as e:
            print(f"  [WARN] Succión: {e}")

# ── Limpiar alarma ────────────────────────────────────────────────────────────
def limpiar_alarma(robot):
    try:
        robot.clear_alarms()
        time.sleep(ALARM_CLEAR_WAIT)
        print("  [ALARMA] Limpiada con clear_alarms() ✓")
        return True
    except AttributeError:
        pass
    try:
        robot._set_cmd(20, b"")
        time.sleep(ALARM_CLEAR_WAIT)
        print("  [ALARMA] Limpiada con comando 20 ✓")
        return True
    except Exception as e:
        print(f"  [ALARMA] No se pudo limpiar: {e}")
        return False

# ── Movimiento atómico a un punto ─────────────────────────────────────────────
def _move(robot, x, y, z, r):
    """Llamada directa a move_to. Lanza excepción si falla."""
    robot.move_to(
        x, y, z, r,
        velocity=VELOCIDAD,
        acceleration=ACELERACION,
        wait=True,
    )

def ir_a_safe(robot):
    sp = SAFE_POINT
    print(f"  ↳ Yendo a SAFE_POINT ({sp['x']}, {sp['y']}, {sp['z']})…")
    try:
        _move(robot, sp["x"], sp["y"], sp["z"], sp["r"])
        return True
    except Exception as e:
        print(f"  [ERROR] SAFE_POINT falló: {e}")
        return False

def mover_punto(robot, punto, idx):
    """
    Mueve al punto dado.
    Flujo:
      1. Valida workspace.
      2. move_to() directo.
      3. Si falla → limpia alarma → reintenta vía SAFE_POINT.
    Devuelve (llegó: bool, robot).
    """
    x, y, z, r = punto["x"], punto["y"], punto["z"], punto["r"]
    print(f"\n  → Punto {idx}: X={x:7.2f}  Y={y:7.2f}  Z={z:7.2f}  R={r:6.2f}")

    # ── 1. Validación ─────────────────────────────────────────
    alcanzable, razon = punto_alcanzable(x, y, z)
    if not alcanzable:
        print(f"  [WARN] Fuera de workspace: {razon}")
        print(f"         Intentando vía SAFE_POINT…")
        if not ir_a_safe(robot):
            print(f"  ✗ Punto {idx} omitido (SAFE_POINT inalcanzable)")
            return False, robot
        # intentar destino después del safe
        try:
            _move(robot, x, y, z, r)
            print(f"     ✓ Llegó al punto {idx} (vía SAFE)")
            return True, robot
        except Exception as e:
            print(f"  ✗ Punto {idx} omitido incluso vía SAFE: {e}")
            return False, robot

    # ── 2. Movimiento directo ─────────────────────────────────
    try:
        _move(robot, x, y, z, r)
        print(f"     ✓ Llegó al punto {idx}")
        return True, robot

    except Exception as e:
        print(f"  [ERROR] Fallo movimiento: {e}")

    # ── 3. Recuperación ───────────────────────────────────────
    print(f"  [RECOVER] Intentando limpiar alarma y reintentar…")
    if limpiar_alarma(robot):
        if not ir_a_safe(robot):
            print(f"  ✗ Punto {idx} omitido (no se pudo recuperar)")
            return False, robot
        try:
            _move(robot, x, y, z, r)
            print(f"     ✓ Llegó al punto {idx} (recuperado)")
            return True, robot
        except Exception as e2:
            print(f"  ✗ Reintento fallido: {e2}")

    print(f"  ✗ Punto {idx} omitido")
    return False, robot

# ── Ejecución de rutina ───────────────────────────────────────────────────────
def ejecutar_rutina(robot, puntos, num):
    total   = len(puntos)
    errores = 0

    print(f"\n{'─'*55}")
    print(f"  EJECUTANDO RUTINA {num}  ({total} puntos)")
    print(f"{'─'*55}")

    for idx, punto in enumerate(puntos):

        # Aplicar succión ANTES del movimiento
        set_suction(robot, punto.get("suction", False))

        llegó, robot = mover_punto(robot, punto, idx)

        if not llegó:
            errores += 1

    # Apagar succión al terminar
    set_suction(robot, False)

    print(f"\n{'─'*55}")
    if errores == 0:
        print(f"  ✓ Rutina {num} completada sin errores")
    else:
        print(f"  ⚠ Rutina {num} completada — {errores}/{total} punto(s) omitido(s)")
    print(f"{'─'*55}")

# ── Menú ──────────────────────────────────────────────────────────────────────
def menu(rutinas):
    print("\n+================================================+")
    print("|     DOBOT EJECUTAR RUTINAS  (pydobotplus)     |")
    print("+================================================+")

    if not rutinas:
        print("  No hay rutinas grabadas.")
        print("  Usa teach_mode.py para grabarlas primero.")
        sys.exit(0)

    for num, desc in SLOT_INFO.items():
        if num in rutinas:
            pts = len(rutinas[num])
            print(f"  [{num}]  {desc:<22}  ({pts} puntos)")
        else:
            print(f"  [{num}]  {desc:<22}  [sin grabar]")

    print("\n  [0] Salir\n")

    op = input("Opción: ").strip()

    if op == '0':
        print("Saliendo…")
        sys.exit(0)

    if op not in rutinas:
        if op in SLOT_INFO:
            print(f"\n[INFO] La rutina {op} no está grabada todavía.")
        else:
            print("\n[INFO] Opción no válida.")
        return None

    return op

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    rutinas = cargar_rutinas()

    op = menu(rutinas)
    if op is None:
        return

    puntos = rutinas[op]

    print(f"\n[RUN] Conectando a Dobot en {PORT}…")
    try:
        robot = Dobot(port=PORT, verbose=False)
    except Exception as e:
        print(f"[ERROR] No se pudo conectar: {e}")
        sys.exit(1)

    print("[RUN] Conectado ✓\n")

    try:
        ejecutar_rutina(robot, puntos, op)
    except KeyboardInterrupt:
        print("\n\n[RUN] Interrumpido por usuario")
        set_suction(robot, False)
    finally:
        try:
            robot.close()
            print("[RUN] Robot desconectado")
        except Exception:
            pass


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nSaliendo…")
        sys.exit(0)

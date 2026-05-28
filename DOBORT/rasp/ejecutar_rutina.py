"""
ejecutar_rutina.py
────────────────────────────────────────────────────────────────
Ejecuta rutinas guardadas del Dobot Magician.

Estrategia de llegada:
  1. move_to normal  → espera confirmación de posición
  2. Si no llegó     → hasta MAX_RAMPAS intentos con corrección
                       incremental (empuja más allá del target
                       proporcionalmente al error restante)
  3. Si tras las rampas el error sigue > MAX_CORRECCION_MM
     o > MAX_CORRECCION_R → para la rutina (seguro)
────────────────────────────────────────────────────────────────
"""

import json
import math
import sys
import time

import pydobot

# ── Configuración ─────────────────────────────────────────────
PORT            = "/dev/ttyAMA0"
RUTINAS_FILE    = "rutinas.json"

TOL_XYZ         = 2.0    # mm  – tolerancia de posición XYZ
TOL_R           = 1.0    # °   – tolerancia de rotación R
TIMEOUT_MOV     = 15.0   # s   – tiempo máximo por movimiento
SETTLE_TIME     = 0.35   # s   – pausa tras llegar antes de succión
SUCTION_WAIT    = 0.4    # s   – pausa tras cambiar estado de succión
POLL_INTERVAL   = 0.08   # s   – cada cuánto se re-verifica posición

MAX_RAMPAS      = 5      # intentos de corrección incremental
RAMPA_FACTOR    = 1.4    # cuánto "más allá" del target se empuja (1.4 = 40% extra)
MAX_CORRECCION_MM = 20.0 # mm – si el error inicial es mayor, para (problema mecánico)
MAX_CORRECCION_R  = 10.0 # °  – igual para rotación


# ── Helpers ───────────────────────────────────────────────────

def cargar_rutinas():
    try:
        with open(RUTINAS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"[ERROR] rutinas.json tiene un error de sintaxis: {e}")
        print("  Revisa el archivo con un validador JSON (jsonlint.com).")
        sys.exit(1)
    except FileNotFoundError:
        print(f"[ERROR] No se encontró '{RUTINAS_FILE}'")
        sys.exit(1)


def get_pose(robot):
    pose = robot.pose()
    return pose[0], pose[1], pose[2], pose[3]


def distancia_xyz(ax, ay, az, bx, by, bz):
    return math.sqrt((ax - bx)**2 + (ay - by)**2 + (az - bz)**2)


def set_suction(robot, enable: bool):
    try:
        robot.suck(enable=enable)
    except TypeError:
        robot.suck(enable)


def esperar_llegada(robot, tx, ty, tz, tr):
    """
    Espera activa hasta llegar al target o agotar TIMEOUT_MOV.
    Devuelve (llegó: bool, cx, cy, cz, cr) — posición final real.
    """
    t0 = time.time()
    while True:
        cx, cy, cz, cr = get_pose(robot)
        d_xyz = distancia_xyz(cx, cy, cz, tx, ty, tz)
        d_r   = abs(cr - tr)

        if d_xyz <= TOL_XYZ and d_r <= TOL_R:
            return True, cx, cy, cz, cr

        if time.time() - t0 > TIMEOUT_MOV:
            return False, cx, cy, cz, cr

        time.sleep(POLL_INTERVAL)


def mover_con_rampa(robot, tx, ty, tz, tr, idx):
    """
    Mueve al target. Si no llega, aplica corrección incremental
    empujando más allá del target en proporción al error restante.

    Devuelve True si llegó dentro de tolerancia, False si no.
    Lanza RuntimeError si el error inicial es demasiado grande
    (señal de problema mecánico, no de inercia).
    """

    print(f"\n  → Punto {idx}: X={tx} Y={ty} Z={tz} R={tr}")

    # ── Intento normal ────────────────────────────────────────
    robot.move_to(tx, ty, tz, tr, wait=True)
    llegó, cx, cy, cz, cr = esperar_llegada(robot, tx, ty, tz, tr)

    if llegó:
        print(f"     ✓ Llegó en intento normal")
        return True

    # ── Calcular error inicial ────────────────────────────────
    ex = tx - cx
    ey = ty - cy
    ez = tz - cz
    er = tr - cr
    error_xyz = distancia_xyz(cx, cy, cz, tx, ty, tz)
    error_r   = abs(er)

    print(
        f"     ! No llegó. Error: XYZ={error_xyz:.1f}mm  R={error_r:.1f}°\n"
        f"       Se quedó en: X={cx:.1f} Y={cy:.1f} Z={cz:.1f} R={cr:.1f}"
    )

    # ── Verificar si el error es razonable para corregir ─────
    if error_xyz > MAX_CORRECCION_MM or error_r > MAX_CORRECCION_R:
        raise RuntimeError(
            f"Error demasiado grande (XYZ={error_xyz:.1f}mm, R={error_r:.1f}°). "
            f"Límites: {MAX_CORRECCION_MM}mm / {MAX_CORRECCION_R}°. "
            f"Posible problema mecánico — rutina detenida."
        )

    # ── Rampas de corrección incremental ─────────────────────
    for intento in range(1, MAX_RAMPAS + 1):

        # Posición donde está ahora
        cx, cy, cz, cr = get_pose(robot)

        # Error restante
        ex = tx - cx
        ey = ty - cy
        ez = tz - cz
        er = tr - cr

        # Target corregido: target + factor * error_restante
        # (empuja un poco más allá para vencer inercia/fricción)
        nx = tx + ex * (RAMPA_FACTOR - 1)
        ny = ty + ey * (RAMPA_FACTOR - 1)
        nz = tz + ez * (RAMPA_FACTOR - 1)
        nr = tr + er * (RAMPA_FACTOR - 1)

        print(
            f"     Rampa {intento}/{MAX_RAMPAS}: "
            f"error XYZ={distancia_xyz(cx,cy,cz,tx,ty,tz):.1f}mm  R={abs(er):.1f}°  →  "
            f"empujando a X={nx:.1f} Y={ny:.1f} Z={nz:.1f} R={nr:.1f}"
        )

        robot.move_to(nx, ny, nz, nr, wait=True)

        # Después del empuje, verificar si ya está en el target real
        llegó, cx, cy, cz, cr = esperar_llegada(robot, tx, ty, tz, tr)

        if llegó:
            print(f"     ✓ Llegó en rampa {intento}")
            # Si el empuje lo llevó más allá, volver al target exacto
            d = distancia_xyz(cx, cy, cz, tx, ty, tz)
            if d > TOL_XYZ:
                robot.move_to(tx, ty, tz, tr, wait=True)
                esperar_llegada(robot, tx, ty, tz, tr)
            return True

    # ── Agotó todas las rampas ────────────────────────────────
    cx, cy, cz, cr = get_pose(robot)
    error_final = distancia_xyz(cx, cy, cz, tx, ty, tz)
    print(
        f"     ✗ No llegó tras {MAX_RAMPAS} rampas. "
        f"Error final: {error_final:.1f}mm"
    )
    return False


# ── Ejecutor principal ────────────────────────────────────────

def ejecutar(rutina_num: str, puntos: list):

    print(f"\nConectando al Dobot en {PORT}…")
    try:
        robot = pydobot.Dobot(port=PORT, verbose=False)
    except Exception as e:
        print(f"[ERROR] No se pudo conectar: {e}")
        sys.exit(1)
    print("Conectado.\n")

    suction_actual = False
    set_suction(robot, False)

    try:
        for i, p in enumerate(puntos):
            tx, ty, tz, tr = p["x"], p["y"], p["z"], p["r"]
            suction_nuevo  = p["suction"]

            # ── Mover con corrección de rampa ─────────────────
            try:
                llegó = mover_con_rampa(robot, tx, ty, tz, tr, i)
            except RuntimeError as e:
                print(f"\n[PARO DE SEGURIDAD] {e}")
                break

            if not llegó:
                print(
                    f"\n[PARO] El brazo no llegó al punto {i} "
                    f"tras {MAX_RAMPAS} rampas. Rutina detenida."
                )
                break

            # ── Succión ───────────────────────────────────────
            time.sleep(SETTLE_TIME)

            if suction_nuevo != suction_actual:
                estado = "ON" if suction_nuevo else "OFF"
                print(f"     Succión → {estado}")
                set_suction(robot, suction_nuevo)
                suction_actual = suction_nuevo
                time.sleep(SUCTION_WAIT)

    except KeyboardInterrupt:
        print("\n\n[INTERRUMPIDO] Apagando succión y cerrando…")

    finally:
        set_suction(robot, False)
        robot.close()
        print("\nDobot desconectado.")

    print(f"\n✓ Rutina {rutina_num} finalizada.")


# ── Entrada ───────────────────────────────────────────────────

if __name__ == "__main__":

    rutinas = cargar_rutinas()

    print("\nRutinas disponibles:")
    for nombre in sorted(rutinas.keys(), key=lambda k: int(k) if k.isdigit() else k):
        n = len(rutinas[nombre])
        print(f"  [{nombre}]  ({n} puntos)")

    rutina_num = input("\nNúmero de rutina a ejecutar: ").strip()

    if rutina_num not in rutinas:
        print(f"[ERROR] Rutina '{rutina_num}' no encontrada.")
        sys.exit(1)

    puntos = rutinas[rutina_num]
    print(f"\nRutina {rutina_num}: {len(puntos)} puntos")

    ejecutar(rutina_num, puntos)

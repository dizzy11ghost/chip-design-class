"""
ejecutar_rutina.py  v4
────────────────────────────────────────────────────────────────
Ejecuta rutinas del Dobot Magician con interpolación automática.

Si el salto entre dos puntos es muy grande, lo divide en
segmentos más pequeños y los ejecuta uno por uno en línea recta.
El número de segmentos se calcula según el eje que más cambie.

Jerarquía de manejo de errores:
  1. Interpolación automática  → divide saltos grandes
  2. Espera activa             → verifica llegada real
  3. Rampas de corrección      → empuje incremental si no llegó
  4. Reconexión automática     → si el Dobot corta comunicación
  5. Paro de seguridad         → si nada funciona
────────────────────────────────────────────────────────────────
"""

import json
import math
import sys
import time

import pydobot

# ── Configuración ─────────────────────────────────────────────
PORT              = "/dev/ttyAMA0"
RUTINAS_FILE      = "rutinas.json"

TOL_XYZ           = 2.0    # mm – tolerancia posición
TOL_R             = 1.0    # °  – tolerancia rotación
TIMEOUT_MOV       = 15.0   # s  – timeout por segmento
SETTLE_TIME       = 0.35   # s  – pausa antes de cambiar succión
SUCTION_WAIT      = 0.4    # s  – pausa tras cambiar succión
POLL_INTERVAL     = 0.08   # s  – frecuencia de polling

# Interpolación — tamaño máximo de cada segmento
SEG_MAX_XYZ       = 40.0   # mm – máximo salto XYZ por segmento
SEG_MAX_Z         = 30.0   # mm – máximo salto Z por segmento (más conservador)
SEG_MAX_R         = 15.0   # °  – máximo salto R por segmento

# Rampas
MAX_RAMPAS        = 5
RAMPA_FACTOR      = 1.4
MAX_CORRECCION_MM = 20.0
MAX_CORRECCION_R  = 10.0

# Reconexión
MAX_RECONEXIONES  = 3
PAUSA_RECONEXION  = 2.0


# ── Interpolación ─────────────────────────────────────────────

def calcular_segmentos(ax, ay, az, ar, bx, by, bz, br):
    """
    Calcula cuántos segmentos se necesitan para ir de A a B
    sin exceder los límites por segmento.
    Devuelve lista de puntos intermedios incluyendo B (no incluye A).
    """
    d_xyz = math.sqrt((bx-ax)**2 + (by-ay)**2 + (bz-az)**2)
    d_z   = abs(bz - az)
    d_r   = abs(br - ar)

    # Número de segmentos necesario según cada eje
    n_xyz = math.ceil(d_xyz / SEG_MAX_XYZ) if d_xyz > SEG_MAX_XYZ else 1
    n_z   = math.ceil(d_z   / SEG_MAX_Z)   if d_z   > SEG_MAX_Z   else 1
    n_r   = math.ceil(d_r   / SEG_MAX_R)   if d_r   > SEG_MAX_R   else 1

    n = max(n_xyz, n_z, n_r)   # el eje más restrictivo manda

    if n == 1:
        return [(bx, by, bz, br)]  # sin interpolación necesaria

    puntos = []
    for i in range(1, n + 1):
        t = i / n
        px = ax + (bx - ax) * t
        py = ay + (by - ay) * t
        pz = az + (bz - az) * t
        pr = ar + (br - ar) * t
        puntos.append((
            round(px, 2),
            round(py, 2),
            round(pz, 2),
            round(pr, 2)
        ))

    return puntos


# ── Conexión ──────────────────────────────────────────────────

def conectar():
    return pydobot.Dobot(port=PORT, verbose=False)


def reconectar(robot_viejo):
    try:
        robot_viejo.close()
    except Exception:
        pass

    for intento in range(1, MAX_RECONEXIONES + 1):
        print(f"  [RECONEXIÓN] Intento {intento}/{MAX_RECONEXIONES}…")
        time.sleep(PAUSA_RECONEXION)
        try:
            robot = conectar()
            print("  [RECONEXIÓN] ✓ Reconectado")
            return robot
        except Exception as e:
            print(f"  [RECONEXIÓN] Falló: {e}")
    return None


# ── Movimiento ────────────────────────────────────────────────

def get_pose(robot):
    pose = robot.pose()
    return pose[0], pose[1], pose[2], pose[3]


def distancia_xyz(ax, ay, az, bx, by, bz):
    return math.sqrt((ax-bx)**2 + (ay-by)**2 + (az-bz)**2)


def set_suction(robot, enable: bool):
    try:
        robot.suck(enable=enable)
    except TypeError:
        robot.suck(enable)


def cmd_move(robot, x, y, z, r):
    """Envía move_to capturando el NoneType error del Dobot."""
    try:
        robot.move_to(x, y, z, r, wait=True)
        return True
    except AttributeError as e:
        if "NoneType" in str(e) or "params" in str(e):
            print(f"  [ERROR SERIAL] Dobot no respondió: {e}")
        else:
            print(f"  [ERROR] {e}")
        return False
    except Exception as e:
        print(f"  [ERROR] move_to: {e}")
        return False


def esperar_llegada(robot, tx, ty, tz, tr):
    t0 = time.time()
    while True:
        try:
            cx, cy, cz, cr = get_pose(robot)
        except Exception:
            return False, tx, ty, tz, tr

        if (distancia_xyz(cx, cy, cz, tx, ty, tz) <= TOL_XYZ
                and abs(cr - tr) <= TOL_R):
            return True, cx, cy, cz, cr

        if time.time() - t0 > TIMEOUT_MOV:
            return False, cx, cy, cz, cr

        time.sleep(POLL_INTERVAL)


def mover_segmento(robot, tx, ty, tz, tr, etiqueta=""):
    """
    Mueve a un único punto con rampas si no llega.
    Devuelve (llegó: bool, robot).
    """
    ok = cmd_move(robot, tx, ty, tz, tr)

    if not ok:
        print(f"  [WARN] {etiqueta} Reconectando…")
        robot = reconectar(robot)
        if robot is None:
            raise ConnectionError("No se pudo reconectar.")
        ok = cmd_move(robot, tx, ty, tz, tr)
        if not ok:
            raise ConnectionError("Dobot no responde tras reconexión.")

    llegó, cx, cy, cz, cr = esperar_llegada(robot, tx, ty, tz, tr)
    if llegó:
        return True, robot

    # ── Rampas ───────────────────────────────────────────────
    error_xyz = distancia_xyz(cx, cy, cz, tx, ty, tz)
    error_r   = abs(tr - cr)

    print(
        f"  {etiqueta} No llegó. "
        f"Error XYZ={error_xyz:.1f}mm  R={error_r:.1f}°  "
        f"(en X={cx:.1f} Y={cy:.1f} Z={cz:.1f})"
    )

    if error_xyz > MAX_CORRECCION_MM or error_r > MAX_CORRECCION_R:
        raise RuntimeError(
            f"Error demasiado grande ({error_xyz:.1f}mm). "
            f"Posible problema mecánico."
        )

    for intento in range(1, MAX_RAMPAS + 1):
        cx, cy, cz, cr = get_pose(robot)
        ex, ey, ez, er = tx-cx, ty-cy, tz-cz, tr-cr

        nx = tx + ex * (RAMPA_FACTOR - 1)
        ny = ty + ey * (RAMPA_FACTOR - 1)
        nz = tz + ez * (RAMPA_FACTOR - 1)
        nr = tr + er * (RAMPA_FACTOR - 1)

        print(
            f"  Rampa {intento}/{MAX_RAMPAS}: "
            f"error={distancia_xyz(cx,cy,cz,tx,ty,tz):.1f}mm → "
            f"empuje X={nx:.1f} Y={ny:.1f} Z={nz:.1f}"
        )

        ok = cmd_move(robot, nx, ny, nz, nr)
        if not ok:
            robot = reconectar(robot)
            if robot is None:
                raise ConnectionError("No se pudo reconectar en rampa.")
            continue

        llegó, cx, cy, cz, cr = esperar_llegada(robot, tx, ty, tz, tr)
        if llegó:
            print(f"  ✓ Llegó en rampa {intento}")
            if distancia_xyz(cx, cy, cz, tx, ty, tz) > TOL_XYZ:
                cmd_move(robot, tx, ty, tz, tr)
                esperar_llegada(robot, tx, ty, tz, tr)
            return True, robot

    return False, robot


def mover_con_interpolacion(robot, ax, ay, az, ar,
                             tx, ty, tz, tr, idx):
    """
    Calcula los segmentos necesarios entre A y B y los ejecuta.
    Devuelve (llegó: bool, robot).
    """
    segmentos = calcular_segmentos(ax, ay, az, ar, tx, ty, tz, tr)
    n = len(segmentos)

    if n == 1:
        etiqueta = f"→ Punto {idx}:"
        print(f"\n  → Punto {idx}: X={tx} Y={ty} Z={tz} R={tr}")
    else:
        print(
            f"\n  → Punto {idx}: X={tx} Y={ty} Z={tz} R={tr}  "
            f"[interpolando en {n} segmentos]"
        )

    for s, (sx, sy, sz, sr) in enumerate(segmentos):
        es_final = (s == n - 1)

        if n > 1:
            etiqueta = f"   seg {s+1}/{n}:"
            print(f"  {etiqueta} X={sx} Y={sy} Z={sz} R={sr}")
        else:
            etiqueta = f"→ Punto {idx}:"

        llegó, robot = mover_segmento(robot, sx, sy, sz, sr, etiqueta)

        if not llegó:
            print(f"  ✗ No llegó al segmento {s+1}/{n} del punto {idx}")
            return False, robot

        if es_final:
            print(f"     ✓ Llegó al punto {idx}")

    return True, robot


# ── Cargar JSON ───────────────────────────────────────────────

def cargar_rutinas():
    try:
        with open(RUTINAS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"[ERROR] rutinas.json tiene error de sintaxis: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"[ERROR] No se encontró '{RUTINAS_FILE}'")
        sys.exit(1)


# ── Ejecutor ──────────────────────────────────────────────────

def ejecutar(rutina_num: str, puntos: list):

    # Preview de interpolaciones necesarias
    print("\nAnalizando rutina…")
    total_segs = 0
    for i in range(1, len(puntos)):
        a, b = puntos[i-1], puntos[i]
        segs = calcular_segmentos(
            a["x"], a["y"], a["z"], a["r"],
            b["x"], b["y"], b["z"], b["r"]
        )
        n = len(segs)
        total_segs += n
        if n > 1:
            dz  = abs(b["z"] - a["z"])
            dxy = math.sqrt((b["x"]-a["x"])**2 + (b["y"]-a["y"])**2)
            print(
                f"  Punto {i}: salto XYZ={dxy:.0f}mm  Z={dz:.0f}mm "
                f"→ dividido en {n} segmentos"
            )

    print(
        f"  Total: {len(puntos)} puntos originales → "
        f"{total_segs} movimientos tras interpolación"
    )

    # Conectar
    print(f"\nConectando al Dobot en {PORT}…")
    try:
        robot = conectar()
    except Exception as e:
        print(f"[ERROR] No se pudo conectar: {e}")
        sys.exit(1)
    print("Conectado.\n")

    suction_actual = False
    set_suction(robot, False)

    # Posición actual como punto de partida para interpolación
    try:
        cx, cy, cz, cr = get_pose(robot)
    except Exception:
        cx, cy, cz, cr = puntos[0]["x"], puntos[0]["y"], puntos[0]["z"], puntos[0]["r"]

    try:
        for i, p in enumerate(puntos):
            tx, ty, tz, tr = p["x"], p["y"], p["z"], p["r"]
            suction_nuevo  = p["suction"]

            try:
                llegó, robot = mover_con_interpolacion(
                    robot,
                    cx, cy, cz, cr,   # desde donde está ahora
                    tx, ty, tz, tr,   # hasta el target
                    i
                )
            except ConnectionError as e:
                print(f"\n[PARO] Conexión perdida: {e}")
                break
            except RuntimeError as e:
                print(f"\n[PARO DE SEGURIDAD] {e}")
                break

            if not llegó:
                print(f"\n[PARO] No llegó al punto {i}. Rutina detenida.")
                break

            # Actualizar posición actual para siguiente interpolación
            cx, cy, cz, cr = tx, ty, tz, tr

            # Succión — solo cambia si es diferente
            time.sleep(SETTLE_TIME)
            if suction_nuevo != suction_actual:
                estado = "ON" if suction_nuevo else "OFF"
                print(f"     Succión → {estado}")
                set_suction(robot, suction_nuevo)
                suction_actual = suction_nuevo
                time.sleep(SUCTION_WAIT)

    except KeyboardInterrupt:
        print("\n\n[INTERRUMPIDO]")

    finally:
        try:
            set_suction(robot, False)
            robot.close()
        except Exception:
            pass
        print("\nDobot desconectado.")

    print(f"\n✓ Rutina {rutina_num} finalizada.")


# ── Main ──────────────────────────────────────────────────────

if __name__ == "__main__":

    rutinas = cargar_rutinas()

    print("\nRutinas disponibles:")
    for nombre in sorted(
        rutinas.keys(),
        key=lambda k: int(k) if k.isdigit() else k
    ):
        n = len(rutinas[nombre])
        print(f"  [{nombre}]  ({n} puntos)")

    rutina_num = input("\nNúmero de rutina a ejecutar: ").strip()

    if rutina_num not in rutinas:
        print(f"[ERROR] Rutina '{rutina_num}' no encontrada.")
        sys.exit(1)

    puntos = rutinas[rutina_num]
    print(f"\nRutina {rutina_num}: {len(puntos)} puntos")

    ejecutar(rutina_num, puntos)

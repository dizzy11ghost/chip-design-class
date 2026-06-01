import math
import time
 
# ── Punto seguro "neutro" ──────────────────────────────────────
# Posición central elevada con buen radio de maniobra.
# AJUSTA según tu setup físico:
SAFE_POINT = {"x": 200.0, "y": 0.0, "z": 80.0, "r": 0.0}
 
# Workspace válido aproximado del Dobot Magician
WS_RADIO_MIN  = 130.0   # mm desde la base (eje Z)
WS_RADIO_MAX  = 320.0   # mm desde la base
WS_Z_MIN      = -70.0   # mm (relativo al origen de la base)
WS_Z_MAX      = 150.0   # mm
 
# Tiempo de espera tras limpiar alarma
ALARM_CLEAR_WAIT = 1.5  # s
 
 
# ── A. Validación cinemática previa ───────────────────────────
 
def punto_alcanzable(x, y, z, r=None):
    """
    Verifica si (x, y, z) está dentro del workspace válido
    del Dobot Magician antes de intentar moverse.
 
    Devuelve (True, "") o (False, "razón").
    """
    radio = math.sqrt(x**2 + y**2)
 
    if radio < WS_RADIO_MIN:
        return False, f"Radio {radio:.1f}mm < mínimo {WS_RADIO_MIN}mm (zona muerta central)"
 
    if radio > WS_RADIO_MAX:
        return False, f"Radio {radio:.1f}mm > máximo {WS_RADIO_MAX}mm (fuera de alcance)"
 
    if z < WS_Z_MIN:
        return False, f"Z={z}mm por debajo del límite {WS_Z_MIN}mm"
 
    if z > WS_Z_MAX:
        return False, f"Z={z}mm por encima del límite {WS_Z_MAX}mm"
 
    return True, ""
 
 
# ── B. Waypoint seguro intermedio ─────────────────────────────
 
def mover_via_safe(robot, tx, ty, tz, tr, idx):
    """
    Mueve el brazo pasando por SAFE_POINT antes del destino.
    Útil cuando el camino directo cruza una singularidad o zona muerta.
 
    Devuelve (llegó: bool, robot).
    """
    sp = SAFE_POINT
    print(f"  ↳ Punto {idx}: vía SAFE ({sp['x']}, {sp['y']}, {sp['z']})")
 
    # Primero al punto seguro
    llegó, robot = mover_segmento(
        robot, sp["x"], sp["y"], sp["z"], sp["r"],
        etiqueta=f"  → Punto {idx} [SAFE]:"
    )
    if not llegó:
        return False, robot
 
    # Luego al destino real
    llegó, robot = mover_segmento(
        robot, tx, ty, tz, tr,
        etiqueta=f"  → Punto {idx} [destino]:"
    )
    return llegó, robot
 
 
# ── C. Recuperación de alarma (luz roja) ──────────────────────
 
def limpiar_alarma(robot):
    """
    Intenta limpiar la alarma activa del Dobot (la que prende
    la luz roja cuando golpea un límite cinemático).
 
    Devuelve True si logró limpiarla.
    """
    try:
        # pydobot expone clear_alarms() en versiones recientes
        robot.clear_alarms()
        time.sleep(ALARM_CLEAR_WAIT)
        print("  [ALARMA] Alarma limpiada con clear_alarms()")
        return True
    except AttributeError:
        pass
 
    # Fallback: algunos builds usan _set_cmd directamente
    try:
        # Comando Dobot 20 = ClearAllAlarmsState
        robot._set_cmd(20, b"")
        time.sleep(ALARM_CLEAR_WAIT)
        print("  [ALARMA] Alarma limpiada con comando directo 20")
        return True
    except Exception as e:
        print(f"  [ALARMA] No se pudo limpiar: {e}")
        return False
 
 
# ── Reemplazo de mover_con_interpolacion ──────────────────────
# Sustituye la función homónima en ejecutar_rutina.py
 
def mover_con_interpolacion(robot, ax, ay, az, ar,
                             tx, ty, tz, tr, idx):
    """
    v2: incluye validación previa y recuperación de alarma.
 
    Flujo:
      1. Valida que el destino esté en workspace válido.
         Si no → registra y usa waypoint seguro de todas formas
                 (el waypoint sí debe ser alcanzable).
      2. Calcula segmentos de interpolación.
      3. Ejecuta cada segmento con mover_segmento().
      4. Si mover_segmento falla con luz roja (error de comm
         o timeout), intenta limpiar la alarma y reintentar
         vía SAFE_POINT una sola vez.
 
    Devuelve (llegó: bool, robot).
    """
 
    # ── 1. Validación previa ──────────────────────────────────
    alcanzable, razon = punto_alcanzable(tx, ty, tz, tr)
    if not alcanzable:
        print(f"\n  [WARN] Punto {idx} fuera de workspace: {razon}")
        print(f"         Intentando ruta alternativa vía SAFE_POINT...")
        llegó, robot = mover_via_safe(robot, tx, ty, tz, tr, idx)
        if llegó:
            print(f"     ✓ Llegó al punto {idx} (vía SAFE)")
        else:
            print(f"  ✗ No llegó al punto {idx} ni vía SAFE. Punto omitido.")
        return llegó, robot
 
    # ── 2. Segmentos normales ─────────────────────────────────
    segmentos = calcular_segmentos(ax, ay, az, ar, tx, ty, tz, tr)
    n = len(segmentos)
 
    if n == 1:
        print(f"\n  → Punto {idx}: X={tx} Y={ty} Z={tz} R={tr}")
    else:
        print(
            f"\n  → Punto {idx}: X={tx} Y={ty} Z={tz} R={tr}  "
            f"[interpolando en {n} segmentos]"
        )
 
    # ── 3. Ejecutar segmentos ─────────────────────────────────
    for s, (sx, sy, sz, sr) in enumerate(segmentos):
        es_final = (s == n - 1)
 
        if n > 1:
            etiqueta = f"   seg {s+1}/{n}:"
            print(f"  {etiqueta} X={sx} Y={sy} Z={sz} R={sr}")
        else:
            etiqueta = f"→ Punto {idx}:"
 
        llegó, robot = mover_segmento(robot, sx, sy, sz, sr, etiqueta)
 
        # ── 4. Recuperación de alarma ─────────────────────────
        if not llegó:
            print(f"  [ALARMA?] Fallo en seg {s+1}/{n}. Intentando recuperar…")
 
            limpiado = limpiar_alarma(robot)
            if limpiado:
                # Reintento completo vía waypoint seguro
                print(f"  ↳ Reintentando punto {idx} vía SAFE_POINT…")
                llegó_safe, robot = mover_via_safe(
                    robot, tx, ty, tz, tr, idx
                )
                if llegó_safe:
                    print(f"     ✓ Llegó al punto {idx} (recuperado vía SAFE)")
                    return True, robot
                else:
                    print(f"  ✗ No se pudo recuperar el punto {idx}.")
                    return False, robot
            else:
                print(f"  ✗ No llegó al segmento {s+1}/{n} del punto {idx}")
                return False, robot
 
        if es_final:
            print(f"     ✓ Llegó al punto {idx}")
 
    return True, robot
 

"""
navegacion.py — módulo de navegación feedforward para el carrito.

El ángulo de desviación se calcula con solvePnP usando las esquinas del ArUco
del carrito y su tamaño físico conocido. No requiere calibración con tablero:
se usa una matriz de cámara aproximada basada en el tamaño del frame.

Reemplaza la función carril() y la lógica de NAVEGAR del script principal.
"""

import math
import time
import numpy as np
import cv2

# ─── IDs ArUco ───────────────────────────────────────────────────────────────
ARUCO_CARRO   = 25
ARUCO_BRAZO   = 50
ARUCO_USUARIO = 10

# ─── Tamaño físico del ArUco del carrito (en metros) ─────────────────────────
# Mide el lado del marcador impreso, de borde a borde del cuadro negro exterior.
MARKER_SIZE_M = 0.06   # 6 cm — ajustar si tu marcador es diferente

# ─── Resolución de la cámara ─────────────────────────────────────────────────
FRAME_W = 640
FRAME_H = 480

# ─── Matriz de cámara aproximada ─────────────────────────────────────────────
# Para una cámara sin calibrar, focal ≈ max(w,h) es una estimación razonable
# para ángulos pequeños (~<30°) como los que esperamos aquí.
def _build_camera_matrix(w: int = FRAME_W, h: int = FRAME_H) -> np.ndarray:
    f = max(w, h)
    return np.array([
        [f,  0, w / 2],
        [0,  f, h / 2],
        [0,  0, 1    ],
    ], dtype=np.float64)

CAMERA_MATRIX = _build_camera_matrix()
DIST_COEFFS   = np.zeros((4, 1), dtype=np.float64)

# ─── Esquinas del marcador en coordenadas locales 3D ─────────────────────────
# Origen en el centro, Z apunta hacia la cámara.
# Orden: top-left, top-right, bottom-right, bottom-left (igual que OpenCV).
_h = MARKER_SIZE_M / 2
MARKER_CORNERS_3D = np.array([
    [-_h,  _h, 0],
    [ _h,  _h, 0],
    [ _h, -_h, 0],
    [-_h, -_h, 0],
], dtype=np.float64)

# ─── Zonas de llegada ─────────────────────────────────────────────────────────
PARKING_FRACCION = 0.125

# ─── Umbral de zona muerta ───────────────────────────────────────────────────
ANGULO_MUERTO_DEG = 6.0

# ─── Tabla de ángulo → comando de compensación ───────────────────────────────
# Formato: (umbral_superior_deg, cmd_avanzar, cmd_reversa)
# Se evalúa de arriba hacia abajo; el primer umbral que supere el ángulo gana.
TABLA_COMANDOS = [
    (-25.0,    "KBC", "KBC"),
    (-15.0,    "KBB", "KBB"),
    (-ANGULO_MUERTO_DEG, "KBA", "KBA"),
    ( ANGULO_MUERTO_DEG, "KAA", "KAA"),
    ( 15.0,    "KAB", "KAB"),
    ( 25.0,    "KAC", "KAC"),
    ( math.inf,"KAD", "KAD"),
]


# ─── Estimación de pose ───────────────────────────────────────────────────────

def _estimar_yaw(corners_2d: np.ndarray) -> float | None:
    """
    Dado el array (4, 2) de esquinas en píxeles de un ArUco,
    retorna el ángulo de yaw en grados usando solvePnP.

    Yaw ≈ 0°  → marcador mirando de frente a la cámara (carrito recto).
    Yaw > 0°  → girado a la derecha.
    Yaw < 0°  → girado a la izquierda.

    Si el ArUco está montado en la parte superior del carrito mirando hacia
    arriba (plano horizontal), el yaw corresponde directamente al ángulo de
    rumbo del carrito. Si está montado vertical (mirando al frente), el yaw
    también funciona pero el signo depende de la orientación de montaje —
    si las correcciones van al revés, negar el valor retornado aquí.
    """
    ok, rvec, _ = cv2.solvePnP(
        MARKER_CORNERS_3D,
        corners_2d.reshape((4, 1, 2)),
        CAMERA_MATRIX,
        DIST_COEFFS,
        flags=cv2.SOLVEPNP_IPPE_SQUARE,
    )
    if not ok:
        return None

    R, _ = cv2.Rodrigues(rvec)

    # Extraer yaw de la matriz de rotación (rotación en plano XZ de la cámara)
    sy = math.sqrt(R[0, 0]**2 + R[1, 0]**2)
    if sy > 1e-6:
        yaw = math.degrees(math.atan2(R[1, 0], R[0, 0]))
    else:
        yaw = 0.0

    return yaw


# ─── API pública ─────────────────────────────────────────────────────────────

def calcular_angulo_pose(corners_dict: dict, id_carro: int) -> float | None:
    """
    Retorna el yaw del carrito en grados, o None si no está visible.

    corners_dict: {marker_id: np.ndarray shape (4,2)} — ver integración abajo.
    """
    if id_carro not in corners_dict:
        return None
    return _estimar_yaw(corners_dict[id_carro])


def elegir_comando(angulo: float, es_avanzar: bool) -> str:
    """
    Mapea el yaw a un comando de compensación PWM de 3 letras.
    """
    for umbral, cmd_av, cmd_rev in TABLA_COMANDOS:
        if angulo < umbral:
            return cmd_av if es_avanzar else cmd_rev
    return "KAA"


def verificar_llegada(posiciones: dict, id_carro: int, id_destino: int,
                       frame_w: int, frame_h: int) -> bool:
    """
    Retorna True cuando el carrito entra en la zona de parking del destino.
    Usa los centros (cx, cy) del detector ArUco original — sin cambios.
    """
    if id_carro not in posiciones:
        return False

    cx, cy, _ = posiciones[id_carro]

    parte  = frame_h // 6
    roa_y1 = 1 * parte
    roa_y2 = 2 * parte
    if not (roa_y1 <= cy < roa_y2):
        return False

    if id_destino == ARUCO_BRAZO:
        return cx < frame_w * PARKING_FRACCION
    else:
        return cx > frame_w * (1.0 - PARKING_FRACCION)


def arrancar_carrito(posiciones: dict, corners_dict: dict, destino_id: int,
                     bt_send_fn, frame_w: int, frame_h: int) -> bool:
    """
    Estima el yaw del carrito, elige el offset de PWM y manda arranque.

    posiciones  : {id: (cx, cy, dist_z)}  — para verificar_llegada
    corners_dict: {id: np.ndarray (4,2)}  — para calcular yaw con solvePnP
    destino_id  : ARUCO_BRAZO o ARUCO_USUARIO
    bt_send_fn  : función bt_send del script principal

    Retorna True si se enviaron los comandos, False si el ArUco no era visible.

    Uso en la FSM (reemplaza el bt_send directo de KUB/KBU):
        ok = arrancar_carrito(posiciones, corners_dict, nav_referencia,
                              bt_send, frame.shape[1], frame.shape[0])
    """
    es_avanzar = (destino_id == ARUCO_BRAZO)

    angulo = calcular_angulo_pose(corners_dict, ARUCO_CARRO)
    if angulo is None:
        print("[NAV] ArUco del carrito no visible — no se puede estimar yaw")
        return False

    cmd_offset   = elegir_comando(angulo, es_avanzar)
    cmd_arranque = "KUB" if es_avanzar else "KBU"

    print(f"[NAV] Yaw estimado: {angulo:.1f}° → offset: {cmd_offset} → arranque: {cmd_arranque}")

    # 1. Offset de PWM (KL25 lo guarda, no arranca todavía)
    bt_send_fn("carro", cmd_offset)
    time.sleep(0.05)
    # 2. Arranque con PWM ya compensado
    bt_send_fn("carro", cmd_arranque)
    return True


# ─── Integración: cambios mínimos en main_rpi.py ─────────────────────────────
#
# 1. Modifica detectar_arucos() para retornar también corners_dict:
#
#       def detectar_arucos(frame):
#           corners, ids, _ = detector.detectMarkers(frame)
#           posiciones   = {}
#           corners_dict = {}                          # ← nuevo
#           if ids is None:
#               return posiciones, corners_dict, frame
#           for i, marker_id in enumerate(ids.flatten()):
#               pts = corners[i].reshape((4, 2))
#               ... # resto igual
#               posiciones[marker_id]   = (cx, cy, distance_z)
#               corners_dict[marker_id] = pts          # ← nuevo
#           return posiciones, corners_dict, frame
#
# 2. En el loop principal:
#       posiciones, corners_dict, frame = detectar_arucos(frame)
#
# 3. Inicializa corners_dict antes del loop:
#       corners_dict = {}
#
# 4. Donde antes mandabas bt_send("carro", "KUB") o bt_send("carro", "KBU"),
#    llama en su lugar:
#       arrancar_carrito(posiciones, corners_dict, nav_referencia,
#                        bt_send, frame.shape[1], frame.shape[0])
#
# 5. El estado NAVEGAR queda exactamente igual, solo cambia carril() por:
#       if verificar_llegada(posiciones, ARUCO_CARRO, nav_referencia, w, h):
#           bt_send("carro", "KST")
#           estado = nav_siguiente_estado

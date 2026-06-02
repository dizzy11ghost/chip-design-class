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
VELOCIDAD       = 100    # mm/s
ACELERACION     = 100    # mm/s²
 
# Umbral de desviación (mm). Si la diferencia entre la posición
# real y la esperada supera este valor en cualquier eje,
# el robot se autocorrige antes de continuar.
UMBRAL_DESVIACION_MM = 2.0
 
# Modo fijo: MOVJ
MODO_MOVIMIENTO = 0x01
 
 
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
 
 
def cargar_rutina(numero):
    """Carga una rutina desde su .json. Retorna (nombre, puntos) o (None, None)."""
    ruta = os.path.join(CARPETA_RUTINAS, f"rutina_{numero:02d}.json")
    if not os.path.exists(ruta):
        return None, None
    with open(ruta, "r") as f:
        data = json.load(f)
    puntos = data.get("rutina", [])
    nombre = data.get("nombre", f"Rutina {numero:02d}")
    if not puntos:
        return nombre, None
    return nombre, puntos
 
 
def obtener_posicion_actual(robot):
    """
    Devuelve la posición actual del robot como dict {x, y, z, r}.
    Retorna None si no se puede leer.
    """
    try:
        pose = robot.get_pose()
        # get_pose() retorna una namedtuple o similar: (x, y, z, r, j1, j2, j3, j4)
        return {"x": pose.x, "y": pose.y, "z": pose.z, "r": pose.r}
    except Exception as e:
        print(f"  [WARN] No se pudo leer la posición actual: {e}")
        return None
 
 
def calcular_desviacion(pos_real, punto_esperado):
    """
    Calcula la desviación máxima en mm entre la posición real
    y la posición esperada del punto anterior.
    Retorna (desviacion_maxima, dict con detalles).
    """
    ejes = ["x", "y", "z"]
    deltas = {eje: abs(pos_real[eje] - punto_esperado[eje]) for eje in ejes}
    desviacion_max = max(deltas.values())
    return desviacion_max, deltas
 
 
# ============================================================
# MENÚ PRINCIPAL
# ============================================================
 
def imprimir_menu_principal():
    os.system("clear")
    print("=" * 55)
    print("   DOBOT MAGICIAN - EJECUTOR DE RUTINAS  [MOVJ]")
    print("=" * 55)
    print(f"  {'#':<5} {'Nombre':<25} {'Puntos':>7}")
    print("  " + "─" * 40)
 
    for i in range(1, TOTAL_RUTINAS + 1):
        nombre, puntos = cargar_rutina(i)
        if nombre and puntos:
            print(f"  {i:<5} {nombre:<25} {len(puntos):>7}")
        elif nombre:
            print(f"  {i:<5} {nombre:<25} {'vacía':>7}")
        else:
            print(f"  {i:<5} {'(sin guardar)':<25} {'─':>7}")
 
    print("  " + "─" * 40)
    print("  [0] Salir")
    print("=" * 55)
 
 
# ============================================================
# EJECUTOR DE RUTINA CON CORRECCIÓN DE POSICIÓN
# ============================================================
 
def ejecutar_rutina(robot, numero):
    nombre, puntos = cargar_rutina(numero)
 
    if not puntos:
        print(f"\n  [!] La rutina {numero:02d} está vacía o no existe.")
        time.sleep(1.5)
        return
 
    os.system("clear")
    print("=" * 55)
    print(f"   EJECUTANDO → Rutina {numero:02d}: {nombre}")
    print("=" * 55)
    print(f"  Modo: MOVJ  |  Umbral corrección: ±{UMBRAL_DESVIACION_MM} mm")
    print(f"  Total de puntos: {len(puntos)}")
 
    # Mostrar resumen de la rutina
    print(f"\n  {'#':<5} {'X':>8} {'Y':>8} {'Z':>8} {'R':>8} {'Succión':>8}")
    print("  " + "─" * 48)
    for i, p in enumerate(puntos):
        suc = "SÍ" if p.get("succion") else "NO"
        print(f"  {i+1:<5} {p['x']:>8} {p['y']:>8} {p['z']:>8} {p['r']:>8} {suc:>8}")
    print()
 
    confirmar = input("  ¿Ejecutar rutina? (s/n): ").strip().lower()
    if confirmar != "s":
        print("  [INFO] Ejecución cancelada.")
        time.sleep(1)
        return
 
    # Configurar velocidad
    robot.speed(velocity=VELOCIDAD, acceleration=ACELERACION)
 
    print(f"\n[INFO] Iniciando rutina '{nombre}' en modo MOVJ...\n")
 
    # Llevar el robot al primer punto antes de arrancar
    # para tener una referencia limpia de posición inicial.
    primer_punto = puntos[0]
    print(f"  [INIT] Desplazando al punto inicial antes de comenzar...")
    try:
        robot.move_to(
            x=primer_punto["x"],
            y=primer_punto["y"],
            z=primer_punto["z"],
            r=primer_punto.get("r", 0),
            wait=True,
            mode=MODO_MOVIMIENTO,
        )
        time.sleep(0.4)
    except Exception as e:
        print(f"  [ERROR] No se pudo alcanzar el punto inicial: {e}")
        input("\n  Presiona ENTER para volver al menú...")
        return
 
    correcciones_totales = 0
 
    try:
        for i, punto in enumerate(puntos):
            x   = punto["x"]
            y   = punto["y"]
            z   = punto["z"]
            r   = punto.get("r", 0)
            suc = punto.get("succion", False)
 
            # ── Verificación de posición ──────────────────────────
            # Antes de ir al punto i, comprobamos que el robot
            # está donde debería estar (en el punto i-1, o en el
            # punto inicial si es el primero).
            pos_real = obtener_posicion_actual(robot)
 
            if pos_real is not None and i > 0:
                punto_anterior = puntos[i - 1]
                desviacion, deltas = calcular_desviacion(pos_real, punto_anterior)
 
                if desviacion > UMBRAL_DESVIACION_MM:
                    correcciones_totales += 1
                    print(
                        f"  [CORRECCIÓN #{correcciones_totales}] Desviación detectada en punto {i} "
                        f"(Δx:{deltas['x']:.1f} Δy:{deltas['y']:.1f} Δz:{deltas['z']:.1f} mm). "
                        f"Reposicionando..."
                    )
                    # Volver al punto anterior para restablecer la referencia
                    robot.move_to(
                        x=punto_anterior["x"],
                        y=punto_anterior["y"],
                        z=punto_anterior["z"],
                        r=punto_anterior.get("r", 0),
                        wait=True,
                        mode=MODO_MOVIMIENTO,
                    )
                    time.sleep(0.3)
                else:
                    print(
                        f"  [{i+1}/{len(puntos)}] ✓ pos. correcta "
                        f"(Δmax:{desviacion:.1f} mm)"
                        f" → X:{x}  Y:{y}  Z:{z}  R:{r}  Succión:{'SÍ' if suc else 'NO'}"
                    )
            else:
                print(f"  [{i+1}/{len(puntos)}] → X:{x}  Y:{y}  Z:{z}  R:{r}  Succión:{'SÍ' if suc else 'NO'}")
 
            # ── Mover al punto destino ────────────────────────────
            robot.move_to(x=x, y=y, z=z, r=r, wait=True, mode=MODO_MOVIMIENTO)
 
            # ── Succión ───────────────────────────────────────────
            robot.suck(suc)
 
            # Pausa de estabilización
            time.sleep(0.3)
 
        print(
            f"\n[OK] Rutina '{nombre}' completada. "
            f"({len(puntos)} puntos | {correcciones_totales} corrección(es) aplicada(s))"
        )
 
    except KeyboardInterrupt:
        print("\n[INFO] Ejecución interrumpida por el usuario.")
        robot.suck(False)   # Apagar succión por seguridad
 
    except Exception as e:
        print(f"\n[ERROR] Fallo durante la ejecución: {e}")
        robot.suck(False)
 
    input("\n  Presiona ENTER para volver al menú...")
 
 
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
 
        while True:
            imprimir_menu_principal()
            entrada = input("\n  Elige una rutina (1-12) o 0 para salir: ").strip()
 
            if entrada == "0":
                print("\n[INFO] Saliendo.\n")
                break
            elif entrada.isdigit() and 1 <= int(entrada) <= TOTAL_RUTINAS:
                ejecutar_rutina(robot, int(entrada))
            else:
                print("  [!] Opción no válida.")
                time.sleep(1)
 
    except KeyboardInterrupt:
        print("\n[INFO] Interrumpido por el usuario.")
 
    except Exception as e:
        print(f"[ERROR] {e}")
 
    finally:
        if robot:
            robot.suck(False)
            robot.close()
            print("[OK] Conexión cerrada.")
 
 
if __name__ == "__main__":
    main()

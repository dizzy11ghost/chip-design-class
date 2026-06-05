from navegacion import arrancar_carrito, verificar_llegada

# Donde antes mandabas bt_send("carro", "KUB"):
arrancar_carrito(posiciones, ARUCO_BRAZO, bt_send, frame.shape[1], frame.shape[0])

# En estado NAVEGAR, reemplaza carril() con:
if verificar_llegada(posiciones, ARUCO_CARRO, nav_referencia, w, h):
    bt_send("carro", "KST")
    estado = nav_siguiente_estado


[BT TX → CARRO] 'KCI'
[NAV] Corrección izquierda enviada: KCI
[BT TX → CARRO] 'KCI'
[NAV] Corrección izquierda enviada: KCI
[BT TX → CARRO] 'KCI'
[NAV] Corrección izquierda enviada: KCI
[BT TX → CARRO] 'KCI'
[NAV] Corrección izquierda enviada: KCI
[BT TX → CARRO] 'KCI'
[NAV] Corrección izquierda enviada: KCI
[BT TX → CARRO] 'KCI'
[NAV] Corrección izquierda enviada: KCI
[BT TX → CARRO] 'KCI'
[NAV] Corrección izquierda enviada: KCI
[BT TX → CARRO] 'KCI'
[NAV] Corrección izquierda enviada: KCI
[BT TX → CARRO] 'KCI'
[NAV] Corrección izquierda enviada: KCI
[BT TX → CARRO] 'KCI'
[NAV] Corrección izquierda enviada: KCI
[BT TX → CARRO] 'KCI'
[NAV] Corrección izquierda enviada: KCI
[BT TX → CARRO] 'KCI'
[NAV] Corrección izquierda enviada: KCI
[BT TX → CARRO] 'KCI'
[NAV] Corrección izquierda enviada: KCI
[BT TX → CARRO] 'KCI'
[NAV] Corrección izquierda enviada: KCI
[BT TX → CARRO] 'KCI'
[NAV] Corrección izquierda enviada: KCI
[BT TX → CARRO] 'KCI'
[NAV] Corrección izquierda enviada: KCI
[BT TX → CARRO] 'KCI'
[NAV] Corrección izquierda enviada: KCI
[BT TX → CARRO] 'KCI'
[NAV] Corrección izquierda enviada: KCI
[BT TX → CARRO] 'KCI'
[NAV] Corrección izquierda enviada: KCI
[FSM] LLEGADA a USUARIO → RUN
[BT TX → CARRO] 'KST'
[DEBUG] rutina_elegida=2 | modo=ACOMODAR
[DOBOT] Ejecutando rutina 02 (18 puntos)
Position(x=156.40000915527344, y=12.960001945495605, z=-39.76000213623047, r=4.75)
Position(x=158.89999389648438, y=11.25, z=-38.459991455078125, r=4.059999942779541)
  [WARN] No se pudo leer posición actual: 'Pose' object has no attribute 'x'
Position(x=158.89999389648438, y=11.25, z=-38.459991455078125, r=4.059999942779541)
  [WARN] No se pudo leer posición actual: 'Pose' object has no attribute 'x'
Position(x=187.52001953125, y=13.280000686645508, z=131.50999450683594, r=4.059999942779541)
  [WARN] No se pudo leer posición actual: 'Pose' object has no attribute 'x'
Position(x=158.489990234375, y=86.0899887084961, z=125.11000061035156, r=28.520000457763672)
  [WARN] No se pudo leer posición actual: 'Pose' object has no attribute 'x'
Position(x=156.6000213623047, y=85.23999786376953, z=83.68000030517578, r=28.56999969482422)
  [WARN] No se pudo leer posición actual: 'Pose' object has no attribute 'x'
Position(x=156.6000213623047, y=85.23999786376953, z=83.68000030517578, r=28.56999969482422)
  [WARN] No se pudo leer posición actual: 'Pose' object has no attribute 'x'
Position(x=156.6000213623047, y=85.23999786376953, z=83.68000030517578, r=28.56999969482422)
  [WARN] No se pudo leer posición actual: 'Pose' object has no attribute 'x'
Position(x=156.6000213623047, y=85.23999786376953, z=83.68000030517578, r=28.56999969482422)
  [WARN] No se pudo leer posición actual: 'Pose' object has no attribute 'x'
Position(x=157.27999877929688, y=85.33000183105469, z=147.7899932861328, r=28.489999771118164)
  [WARN] No se pudo leer posición actual: 'Pose' object has no attribute 'x'
Position(x=82.96000671386719, y=157.74998474121094, z=146.80999755859375, r=62.27000045776367)
  [WARN] No se pudo leer posición actual: 'Pose' object has no attribute 'x'
Position(x=-25.339998245239258, y=174.00997924804688, z=145.4600067138672, r=98.29000091552734)
  [WARN] No se pudo leer posición actual: 'Pose' object has no attribute 'x'
Position(x=-35.00999069213867, y=147.63002014160156, z=35.25001525878906, r=103.3499984741211)
  [WARN] No se pudo leer posición actual: 'Pose' object has no attribute 'x'
Position(x=-35.00999069213867, y=147.63002014160156, z=35.25001525878906, r=103.3499984741211)
  [WARN] No se pudo leer posición actual: 'Pose' object has no attribute 'x'
Position(x=-35.00999069213867, y=147.63002014160156, z=35.25001525878906, r=103.3499984741211)
  [WARN] No se pudo leer posición actual: 'Pose' object has no attribute 'x'
Position(x=-35.00999069213867, y=147.63002014160156, z=35.25001525878906, r=103.3499984741211)
  [WARN] No se pudo leer posición actual: 'Pose' object has no attribute 'x'
Position(x=-35.6400146484375, y=151.1999969482422, z=93.12001037597656, r=103.2699966430664)
  [WARN] No se pudo leer posición actual: 'Pose' object has no attribute 'x'
Position(x=83.11998748779297, y=144.489990234375, z=134.74000549316406, r=60.099998474121094)
  [WARN] No se pudo leer posición actual: 'Pose' object has no attribute 'x'
Position(x=168.19003295898438, y=22.5100040435791, z=135.47000122070312, r=7.630000114440918)
[DOBOT] Rutina 02 completada (0 correcciones)
[BT TX → MASTER] 'ML'
[BT TX → CARRO] 'KBU'
[FSM] Paquete depositado → navegando a usuario
[BT TX → CARRO] 'KCI'
[NAV] Corrección izquierda enviada: KCI
[BT TX → CARRO] 'KCI'
[NAV] Corrección izquierda enviada: KCI
[BT TX → CARRO] 'KCI'
[NAV] Corrección izquierda enviada: KCI
[BT TX → CARRO] 'KCI'
[NAV] Corrección izquierda enviada: KCI
[FSM] LLEGADA a BRAZO → IDLE
[BT TX → CARRO] 'KST'









───────────────────────────────────────────────────────
  GRABANDO RUTINA 6
  AMARILLO – ft6
───────────────────────────────────────────────────────
  ENTER -> guardar posición actual
  s     -> toggle succión
  d     -> borrar último punto
  f     -> finalizar y guardar
  q     -> cancelar
───────────────────────────────────────────────────────

[ERROR] No se pudo leer pose: tuple index out of range

[ERROR] No se pudo leer pose: tuple index out of range

[ERROR] No se pudo leer pose: tuple index out of range



"1": [
    {
      "x": 192.91,
      "y": 56.17,
      "z": 159.49,
      "r": 24.04,
      "suction": falseRutina 1: 41 puntos

Conectando al Dobot en /dev/ttyAMA0…
Conectado.


  → Punto 0: X=192.91 Y=56.17 Z=159.49 R=24.04
     ✓ Llegó en intento normal

  → Punto 1: X=170.97 Y=-29.19 Z=-60.01 R=-1.88

Dobot desconectado.
Traceback (most recent call last):
  File "/home/ingenierinis/GOAT/chip-design-class/DOBORT/pydobot/ejecutar_rutina.py", line 256, in <module>
    ejecutar(rutina_num, puntos)
    ~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/home/ingenierinis/GOAT/chip-design-class/DOBORT/pydobot/ejecutar_rutina.py", line 203, in ejecutar
    llegó = mover_con_rampa(robot, tx, ty, tz, tr, i)
            ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ingenierinis/GOAT/chip-design-class/DOBORT/pydobot/ejecutar_rutina.py", line 104, in mover_con_rampa
    robot.move_to(tx, ty, tz, tr, wait=True)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ingenierinis/GOAT/chip-design-class/DOBORT/pydobot/pydobot/dobot.py", line 307, in move_to
    self._set_ptp_cmd(x, y, z, r, mode=PTPMode.MOVL_XYZ, wait=wait)
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ingenierinis/GOAT/chip-design-class/DOBORT/pydobot/pydobot/dobot.py", line 232, in _set_ptp_cmd
    return self._send_command(msg, wait)
           ~~~~~~~~~~~~~~~~~~^^^^^^^^^^^
  File "/home/ingenierinis/GOAT/chip-design-class/DOBORT/pydobot/pydobot/dobot.py", line 95, in _send_command
    expected_idx = struct.unpack_from('L', response.params, 0)[0]
                                           ^^^^^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'params'
    },
    {
      "x": 170.97,
      "y": -29.19,
      "z": -60.01,
      "r": -1.88,
      "suction": false
    },
    {
      "x": 194.41,
      "y": -33.1,
      "z": -9.31,
      "r": -1.85,
      "suction": false
    },
    {
      "x": 200.54,
      "y": -34.24,
      "z": 74.56,
      "r": -1.88,
      "suction": false
    },
    {
      "x": 198.49,
      "y": -33.89,
      "z": 116.45,
      "r": -1.88,
      "suction": false
    },
    {
      "x": 200.77,
      "y": 8.82,
      "z": 117.11,
      "r": 10.33,
      "suction": false
    },
    {
      "x": 197.09,
      "y": 43.96,
      "z": 115.88,
      "r": 20.38,
      "suction": false
    },
    {
      "x": 182.05,
      "y": 87.0,
      "z": 116.26,
      "r": 33.35,
      "suction": false
    },
    {
      "x": 196.74,
      "y": 93.92,
      "z": 107.74,
      "r": 33.33,
      "suction": false
    },
    {
      "x": 211.96,
      "y": 98.07,
      "z": 94.1,
      "r": 32.64,
      "suction": false
    },
    {
      "x": 223.54,
      "y": 103.43,
      "z": 66.94,
      "r": 32.64,
      "suction": false
    },
    {
      "x": 230.58,
      "y": 102.83,
      "z": 45.74,
      "r": 31.85,
      "suction": false
    },
    {
      "x": 230.55,
      "y": 103.2,
      "z": 37.24,
      "r": 31.93,
      "suction": true
    },
    {
      "x": 219.73,
      "y": 105.14,
      "z": 88.56,
      "r": 33.38,
      "suction": true
    },
    {
      "x": 203.48,
      "y": 103.68,
      "z": 105.7,
      "r": 34.81,
      "suction": true
    },
    {
      "x": 180.48,
      "y": 140.0,
      "z": 102.12,
      "r": 45.61,
      "suction": true
    },
    {
      "x": 159.07,
      "y": 163.39,
      "z": 98.46,
      "r": 53.58,
      "suction": true
    },
    {
      "x": 136.52,
      "y": 180.79,
      "z": 92.73,
      "r": 60.75,
      "suction": true
    },
    {
      "x": 112.78,
      "y": 196.45,
      "z": 90.92,
      "r": 67.95,
      "suction": true
    },
    {
      "x": 76.59,
      "y": 213.34,
      "z": 90.02,
      "r": 78.06,
      "suction": true
    },
    {
      "x": 44.04,
      "y": 223.0,
      "z": 90.79,
      "r": 86.64,
      "suction": true
    },
    {
      "x": 18.27,
      "y": 225.43,
      "z": 85.79,
      "r": 93.18,
      "suction": true
    },
    {
      "x": 15.82,
      "y": 195.26,
      "z": 88.32,
      "r": 93.18,
      "suction": true
    },
    {
      "x": 13.24,
      "y": 164.33,
      "z": 86.03,
      "r": 93.2,
      "suction": true
    },
    {
      "x": 5.17,
      "y": 159.81,
      "z": 67.02,
      "r": 95.96,
      "suction": true
    },
    {
      "x": 5.03,
      "y": 155.43,
      "z": 49.19,
      "r": 95.96,
      "suction": true
    },
    {
      "x": 4.76,
      "y": 151.35,
      "z": 32.76,
      "r": 96.01,
      "suction": false
    },
    {
      "x": 5.18,
      "y": 162.48,
      "z": 56.4,
      "r": 95.98,
      "suction": false
    },
    {
      "x": 9.95,
      "y": 172.05,
      "z": 76.44,
      "r": 94.5,
      "suction": false
    },
    {
      "x": 34.92,
      "y": 175.11,
      "z": 90.28,
      "r": 86.53,
      "suction": false
    },
    {
      "x": 62.78,
      "y": 167.07,
      "z": 89.96,
      "r": 77.22,
      "suction": false
    },
    {
      "x": 101.92,
      "y": 145.73,
      "z": 89.05,
      "r": 62.84,
      "suction": false
    },
    {
      "x": 138.54,
      "y": 112.9,
      "z": 94.77,
      "r": 46.99,
      "suction": false
    },
    {
      "x": 163.28,
      "y": 73.18,
      "z": 95.17,
      "r": 31.95,
      "suction": false
    },
    {
      "x": 171.83,
      "y": 45.31,
      "z": 101.61,
      "r": 22.58,
      "suction": false
    },
    {
      "x": 176.05,
      "y": 10.01,
      "z": 106.28,
      "r": 11.07,
      "suction": false
    },
    {
      "x": 176.15,
      "y": -10.02,
      "z": 106.68,
      "r": 4.55,
      "suction": false
    },
    {
      "x": 180.28,
      "y": -19.14,
      "z": 68.91,
      "r": 1.75,
      "suction": false
    },
    {
      "x": 171.6,
      "y": -18.22,
      "z": 30.82,
      "r": 1.75,
      "suction": false
    },
    {
      "x": 171.6,
      "y": -18.22,
      "z": 30.82,
      "r": 1.75,
      "suction": false
    },
    {
      "x": 166.85,
      "y": -26.27,
      "z": -26.19,
      "r": -1.14,
      "suction": false
    }
  ],


  Rutina 1: 41 puntos

Conectando al Dobot en /dev/ttyAMA0…
Conectado.


  → Punto 0: X=192.91 Y=56.17 Z=159.49 R=24.04
     ✓ Llegó en intento normal

  → Punto 1: X=170.97 Y=-29.19 Z=-60.01 R=-1.88

Dobot desconectado.
Traceback (most recent call last):
  File "/home/ingenierinis/GOAT/chip-design-class/DOBORT/pydobot/ejecutar_rutina.py", line 256, in <module>
    ejecutar(rutina_num, puntos)
    ~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/home/ingenierinis/GOAT/chip-design-class/DOBORT/pydobot/ejecutar_rutina.py", line 203, in ejecutar
    llegó = mover_con_rampa(robot, tx, ty, tz, tr, i)
            ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ingenierinis/GOAT/chip-design-class/DOBORT/pydobot/ejecutar_rutina.py", line 104, in mover_con_rampa
    robot.move_to(tx, ty, tz, tr, wait=True)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ingenierinis/GOAT/chip-design-class/DOBORT/pydobot/pydobot/dobot.py", line 307, in move_to
    self._set_ptp_cmd(x, y, z, r, mode=PTPMode.MOVL_XYZ, wait=wait)
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ingenierinis/GOAT/chip-design-class/DOBORT/pydobot/pydobot/dobot.py", line 232, in _set_ptp_cmd
    return self._send_command(msg, wait)
           ~~~~~~~~~~~~~~~~~~^^^^^^^^^^^
  File "/home/ingenierinis/GOAT/chip-design-class/DOBORT/pydobot/pydobot/dobot.py", line 95, in _send_command
    expected_idx = struct.unpack_from('L', response.params, 0)[0]
                                           ^^^^^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'params'

## DiagramaS de flujo del sistema
Diagrama sistema completo:
<img width="1015" height="972" alt="image" src="https://github.com/user-attachments/assets/b8487263-3fbc-4e14-950b-1612c15813dd" />

Diagrama FSM Raspberry Pi: 
<img width="952" height="926" alt="image" src="https://github.com/user-attachments/assets/93181754-f01d-48a9-9ef8-7c5a2aee3e1e" />

Diagrama mensajes bluetooth:
<img width="1054" height="742" alt="image" src="https://github.com/user-attachments/assets/d374806c-7026-4146-a164-d1ddabf33bb0" />


Link a lugar para hacer los diagramas: https://lucid.app/lucidchart/20e2468b-7871-4546-8c00-b95ea3eb9a92/edit?viewport_loc=6243%2C-1367%2C2546%2C1248%2C0_0&invitationId=inv_3f67f78b-2500-4cd6-b22b-de2e897b06b3


## Pruebas iniciales visión computacional
Primera prueba: test de máscaras para detección de colores rojo, azul y amarillo, destinados a las cajas 
<img width="663" height="751" alt="Captura de pantalla 2026-05-16 214523" src="https://github.com/user-attachments/assets/d36b3435-01f2-4859-8697-a71c47ca201b" />


Traceback (most recent call last):
  File "/home/ingenierinis/GOAT/chip-design-class/DOBORT/pydobot/main_dobot.py", line 22, in <module>
    GPIO.setup(pin, GPIO.IN)
  File "/usr/lib/python3/dist-packages/RPi/GPIO/__init__.py", line 696, in setup
    _check(lgpio.gpio_claim_input(_chip, gpio, {
  File "/usr/lib/python3/dist-packages/lgpio.py", line 755, in gpio_claim_input
    return _u2i(_lgpio._gpio_claim_input(handle&0xffff, lFlags, gpio))
  File "/usr/lib/python3/dist-packages/lgpio.py", line 458, in _u2i
    raise error(error_text(v))
lgpio.error: 'GPIO busy'


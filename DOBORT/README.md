## DiagramaS de flujo del sistema
Diagrama sistema completo:
<img width="1015" height="972" alt="image" src="https://github.com/user-attachments/assets/b8487263-3fbc-4e14-950b-1612c15813dd" />

Diagrama FSM Raspberry Pi: 
<img width="799" height="780" alt="image" src="https://github.com/user-attachments/assets/46ffa5ce-094c-4d5a-9d4f-772b2fe98ff9" />

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

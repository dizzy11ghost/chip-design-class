import RPi.GPIO as GPIO
import time

# ==============================
# CONFIGURACIÓN
# ==============================

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(True)

# Pines FT
PINES_FT = {
    "ft1": 17,
    "ft2": 22,
    "ft3": 23,
    "ft4": 24,
    "ft5": 25,
    "ft6": 27
}

# ==============================
# SETUP GPIO
# ==============================

for nombre, pin in PINES_FT.items():
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    print(f"[INIT] {nombre} -> GPIO {pin}")

print("\n=== TEST GPIO INICIADO ===")
print("Conecta cada pin a GND para probar")
print("CTRL+C para salir\n")

# ==============================
# LOOP PRINCIPAL
# ==============================

try:
    while True:

        print("--------------")

        for nombre, pin in PINES_FT.items():

            valor = GPIO.input(pin)

            estado = ""

            if valor == 1:
                estado = "HIGH / PULL-UP OK / LIBRE"
            else:
                estado = "LOW / CONECTADO A GND"

            print(f"{nombre} (GPIO {pin}) = {valor} ---> {estado}")

        time.sleep(0.5)

except KeyboardInterrupt:
    print("\nSaliendo...")

finally:
    GPIO.cleanup()
    print("GPIO limpio")

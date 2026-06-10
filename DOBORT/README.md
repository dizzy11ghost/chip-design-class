#  ARGO - Sistema Automatizado de Gestión de Paquetes
### Miguel Alonso De La Rosa Zamora  - Sophia Leñero Gómez - Gregorio Alejandro Orozco Torres 
A01646106 - A01639462 - A01641967

## Descripción general
Argo es un sistema de automatización de almacenes diseñado para demostrar la integración de sistemas embebidos, visión computacional, robótica y comunicaciones inalámbricas.

El sistema permite almacenar y recuperar paquetes de manera automática mediante la coordinación de un brazo robótico Dobot Magician, un vehículo móvil autónomo, dos tarjetas FRDM-KL25Z, una Raspberry Pi 5, sensores fotoeléctricos para detección de espacios disponibles y visión computacional para clasificación de paquetes por color.

El objetivo principal es simular el flujo de recepción, almacenamiento y entrega de paquetes dentro de un almacén inteligente.

## Arquitectura del sistema
### Módulo Master (FRDM-KL25Z)
Su función es mostrar menús en pantalla LCD, leer entradas mediante teclado matricial, gestionar solicitudes de almacenamiento, gestionar solicitudes de recuperación, mostrar mensajes de estado, supervisar el botón de paro de emergencia y comunicarse con la Raspberry Pi mediante Bluetooth.

Sistema Operativo:
El módulo utiliza FreeRTOS para dividir responsabilidades en tareas independientes:

Tareas relacionadas a UI:
- Menú principal.
- Solicitudes de almacenamiento.
- Solicitudes de recuperación.
- Mensajes al usuario.

Tarea UART RX
- Recibe mensajes Bluetooth y los almacena en una cola para evitar pérdida de datos.

Tarea Emergencia
- Tiene la máxima prioridad y detiene completamente el sistema cuando se activa el botón de emergencia.

### Módulo Central (Raspberry Pi + Dobot)
Funciones:
- Procesamiento de visión computacional.
- Comunicación con ambos módulos KL25Z.
- Selección de posiciones de almacenamiento.
- Control del Dobot Magician.
- Supervisión de sensores fotoeléctricos.
- Coordinación global del flujo de trabajo.

### Módulo Vehículo Autónomo (FRDM-KL25Z)
Controla el movimiento del carro encargado del transporte de paquetes.
Funciones: 
- Desplazamiento entre usuario y brazo robótico.
- Control de motores DC mediante PWM.
- Corrección de trayectoria usando encoders.
- Comunicación UART/Bluetooth.
- Indicación visual mediante LEDs RGB.

Control de Movimiento:
El vehículo utiliza encoders en ambas ruedas, control proporcional (P), corrección dinámica de velocidad y conteo de pulsos para estimación de distancia. La distancia recorrida se calcula mediante 12.78 pulsos/cm

## Diagramas de flujo del sistema
Diagrama sistema completo:
<img width="1015" height="972" alt="image" src="https://github.com/user-attachments/assets/b8487263-3fbc-4e14-950b-1612c15813dd" />

Diagrama mensajes bluetooth:
<img width="889" height="970" alt="image" src="https://github.com/user-attachments/assets/ee57e6b8-633e-4553-8fdf-4ceb68384c6a" />




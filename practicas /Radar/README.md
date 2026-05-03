#### Miguel Alonso De La Rosa Zamora A01646106 - Gregorio Alejandro Orozco Torres A01641967 - Sophia Leñero Gómez A01639462

# Radar

## Descripción de la práctica
Para esta práctica, teneíamos que implementar un sistema utilizando la tarjeta FRDM KL25z que fuera capaz de funcionar a modo de un radar. Esto por medio del uso de un sensor ultrasónico HC-SR04, un motor a pasos 28BYJ-48 de 5V y la conexión serial UART entre la tarjeta y la computadora. Nuestro sistema estaba separado por dos partes escenciales, la parte codificada en C en MCUExpresso, la cuál debía controlar el motor para que diera vueltas de 360 grados para poder revisar todo su entorno, y la parte del sensor ultrasónico, capaz de detectar obstáculos y su distancia con un umbral de 25 cm, y finalmente mandar esa detección de ángulo, distancia y posición por medio de UART 0. La segunda parte, codificada en Python, tenía que ser capaz de recibir por UART esos valores y plasmarlos en una gráfica que mostrara en dónde estaba el obstáculo detectado.

## Diagrama de flujo
El funcionamiento de ambos códigos se muestra a continuación:
<div align="center">
  <img width="561" height="983" alt="image" src="https://github.com/user-attachments/assets/eea27ab4-22c9-4591-99c7-08902b7c6c22" />
</div>

## Esquemático del circuito utilizado 
<div align="center">
</div>

# Funcionamiento

## Pruebas Individuales
<div align="center">
  <img width=30% height=30% alt="WhatsApp Image 2026-04-30 at 10 30 40 AM" src="https://github.com/user-attachments/assets/12854e17-7bf8-4c10-8f02-f6eddb18d4ac" 
    />
  <img width=30% height=30% alt="WhatsApp Image 2026-04-30 at 10 30 40 AM (1)" src="https://github.com/user-attachments/assets/80825839-280c-46be-a20b-ab080d58273d" 
    />
</div>

## Movimiento

## Grafica
Para graficar, utilizamos matplot lib, la cuál nos permitió crear la siguiente gráfica:
<div align="center">
<img width="1197" height="1292" alt="image" src="https://github.com/user-attachments/assets/d9d182dd-756d-46a5-9e29-f4c0ea7bf767" />
</div>
En esta se muestra en un circulo representando los 360* de alcance que tiene el motor a pasos y muestra un radio de 25 cm, umbral utilizado para el sensor ultrasónico. Al pasar por comunicación serial la distancia y el ángulo es que podemos plasmar el objeto detectado dentro del radar. 

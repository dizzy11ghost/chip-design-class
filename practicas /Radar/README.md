#### Miguel Alonso De La Rosa Zamora A01646106 - Gregorio Alejandro Orozco Torres A01641967 - Sophia Leñero Gómez A01639462

# Mini Challenge: Radar

## Descripción de la práctica
Para esta práctica, teneíamos que implementar un sistema utilizando la tarjeta FRDM KL25z que fuera capaz de funcionar a modo de un radar. Esto por medio del uso de un sensor ultrasónico HC-SR04, un motor a pasos 28BYJ-48 de 5V y la conexión serial UART entre la tarjeta y la computadora. Nuestro sistema estaba separado por dos partes escenciales, la parte codificada en C en MCUExpresso, la cuál debía controlar el motor para que diera vueltas de 360 grados para poder revisar todo su entorno, y la parte del sensor ultrasónico, capaz de detectar obstáculos y su distancia con un umbral de 25 cm, y finalmente mandar esa detección de ángulo, distancia y posición por medio de UART 0. La segunda parte, codificada en Python, tenía que ser capaz de recibir por UART esos valores y plasmarlos en una gráfica que mostrara en dónde estaba el obstáculo detectado.

## Diagrama de flujo
<div align="center">
  ### Código en C de la KL25z:
  <img width="500" height="936" alt="image" src="https://github.com/user-attachments/assets/ccbf7ac2-32f2-4f3b-a426-7cce480119b9" />
  ### Código en Python de la gráfica:
  <img width="507" height="861" alt="image" src="https://github.com/user-attachments/assets/d274da48-432d-420f-a39f-f48426f6831b" />

</div>

## Funcionamiento
Diseñamos el sistema para que fuera capaz de realizar un barrido de 360° utilizando un motor a pasos. El motor hacía una rotación completa en sentido horario, después una rotación completa en sentido antihorario y así indefinidamente, permitiendo así un escaneo completo constante de todo su entorno. Sobre el eje del motor montamos el sensor ultrasónico utilizando un soporte de acrílico, permitiendo así que el sensor pudiera obtener mediciones en cualquier dirección alrededor de él.

El control del motor se logró mediante una secuencia de activación de bobinas definidas en el script, utilizando 4 pines del puerto C de la KL25z. Considerando que al motor le tomaba 512 pasos dar una vuelta completa, podíamos asociar cada paso con una posición angular, permitiendonos calcular  el ángulo de medición del sensor usando una relación proporcional entre los pasos y los 360°. 

Durante cada paso, el sensor realizaba una medición de la distancia usando un pulso de trigger y midiendo el tiempo de retorno de la señal eco mediante el TPM0 de la tarjeta. El tiempo medido era utilizado para calcular la distancia en cm posteriormente. Si el sensor no detectaba ningún objeto, la medición se descartaba, pero si se detectaba algo, se acomodaba la información obtenida respecto al ángulo y la distancia en un par de la forma (ángulo, distancia). 

Estas mediciones eran posteriormente transmitidas en tiempo real a la computadora por medio de la comuniación serial UART0 configurada a 9600 baudios. La tarjeta enviaba constantemente los datos que un programa de Python recibiría e interpretaría desde las lecturas captadas por el puerto al cuál estaba conectada la tarjeta. 

El programa graficador utilizaba la liberería pyserial para recibir los datos seriales y procesarlos en tiempo real, después, usando matplotlib, graficabamos las mediciones en una gráfica polar que simulaba un radar. Cada obstáculo detectado se mostraba usando su ángulo y distancia para plasmarlos en la gráfica como un punto. La gráfica mostraba el rango del motor (360°) y el umbral del sensor (25cm) y mostraba adicionalmente una línea móvil que inficaba la dirección a la que iba el radar. 

## Gráfica
Como expresado anteriormente, utilizamos la librería matplotlib para poder crear una gráfica polar de 360° por 25cm de radio para poder en ella desplegar en tiempo real los obstáculos que el sensor iba detectando y una línea dínámica que permitía visualizar la dirección del motor. La gráfica base se despliega a continuación:
<div align="center">
<img width=50% height=50% alt="image" src="https://github.com/user-attachments/assets/d9d182dd-756d-46a5-9e29-f4c0ea7bf767" />
</div>

## Esquemático
Para realizar esta práctica, se utilizó una tarjeta FRDM KL25z, un sensor ultrasónico HC-SR04 y un motor a pasos 28BYJ-48 de 5V (cómo mencionado anteriormente). 
Las conexiones utilizadas se muestran a continuación:
<div align="center">
  <img width="722" height="489" alt="image" src="https://github.com/user-attachments/assets/420d617f-1eed-41eb-b986-2042628178ca" />
</div>

## Pruebas Individuales
Para poder trabajar de manera más eficiente, trabajamos inicialmente de manera separada la implementación del sensor, el motor y la graficación, después de conseguir resultados exitosos en cada una de estas pruebas, continuamos con la integración.
<div align="center">
  <img width=30% height=30% alt="WhatsApp Image 2026-04-30 at 10 30 40 AM" src="https://github.com/user-attachments/assets/12854e17-7bf8-4c10-8f02-f6eddb18d4ac" 
    />
  <img width=30% height=30% alt="WhatsApp Image 2026-04-30 at 10 30 40 AM (1)" src="https://github.com/user-attachments/assets/80825839-280c-46be-a20b-ab080d58273d" 
    />
</div>

## Integración general
Finalmente, integramos todo en un prototipo final funcional, como se muestra en seguida: 
<div align="center">
<img width=40% height=40% alt="image" src="https://github.com/user-attachments/assets/b05c5f51-f78c-4692-9618-54c4e2306bae" />
</div>
https://github.com/user-attachments/assets/6c865eb6-6c19-49cb-8b2e-65539ae27085





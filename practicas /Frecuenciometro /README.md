#### Miguel Alonso De La Rosa Zamora A01646106 - Gregorio Alejandro Orozco Torres A01641967 - Sophia Leñero Gómez A01639462

# Mini Reto 6 - Frecuenciometro

## Descripción de la práctica
El objetivo de esta práctica era diseñar y construir un frecuencímetro utilizando los timers de un microcontrolador FRDM KL25Z. Este dispositivo sería capaz de medir la frecuencia de una señal de entrada con precisión (+-1%) y mostrar el resultado en un display LCD.

## Funcionamiento del sistema
Para este reto, decidimos utilizarun método que nos permitió simplificar bastante el funcionamiento del sistema. Nuestro enfoque fue implementar un contador de flancos y un cronómetro interno (Internal Reference Clock), esto para poder seguir el principio de que el tiempo transcurrido fuera de 1 segundo para que el número de flancos fuera numéricamente igual a la frecuencia en Hz.

## Diagrama de flujo
<div align="center">
  <img width="548" height="953" alt="image" src="https://github.com/user-attachments/assets/ca265e8f-d034-409a-af5b-a2b3cfbd662d" />
</div>

## Esquemático del circuito utilizado 
Para el circuito utilizado, se hicieron dos versiones, la primera fue para poder probar sacar la frecuencia generada por una tarjeta KL25z con otra tarjeta igual, que es la configuración mostrada en el siguiente esquemático;
<div align="center">
  <img width="1102" height="630" alt="image" src="https://github.com/user-attachments/assets/25b69bf8-922d-4113-b55c-bce3a1cd4ec7" />
</div>
La segunda versión realizada fue con un generador de ondas, como se muestra en la siguiente sección de este reporte.

## Evidencias del funcionamiento de la práctica
Para probar el frecuenciometro utilizamos un generador de ondas, configurandolo a una frecuencia de 1000 Hz y comprobando en el display LCD el valor obtenido. A continuación se muestra un video de la validación revisada;

https://github.com/user-attachments/assets/3372bebf-e621-4244-9b95-ed1378d27851

## Conclusiones y aprendizajes
Esta actividad fue muy valiosa porque nos permitió explorar los diferentes métodos capaces de ayudarnos a obtener de manera constante la frecuencia. El método con el que lo terminamos implementando no fue nuestra primera opción, pero fue la opción que nos permitió tener resultados más limpios al reducir el nivel de complejidad y aumentando el nivel de precisión. 




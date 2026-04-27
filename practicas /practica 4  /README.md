#### Miguel Alonso De La Rosa Zamora A01646106
#### Gregorio Alejandro Orozco Torres A01641967
#### A01639462 Sophia Leñero Gómez

# Práctica 4 - LCD-Keyboard-Timers-Interrupts.docx

# Parte 1
## Descripción del proyecto
Para la primera parte de esta práctica, se utilizó la KL25Z para crear un sistema basado en interrupciones con un botón y dos LEDs, en donde el LED rojo se mantiene parpadeando de forma continua hasta que el usuario presiona un botón. El funcionamiento de este código incluye la configuración del temporizador TPM0 para generar retardos, así como una interrupción en el pin PTA1 que, al activarse, apaga el LED rojo y enciende el LED verde durante un segundo antes de volver a apagarlo, demostrando el uso de interrupciones externas junto con control de LEDs.

## Diagrama de flujo


## Funcionamiento
Fotos del funcionamiento del ejericicio 1 
<img width="1200" height="1600" alt="image" src="https://github.com/user-attachments/assets/e71dddd3-d113-4fc6-8a93-74c8eda53e5c" />
<img width="1200" height="1600" alt="image" src="https://github.com/user-attachments/assets/f45fdd4c-445c-4679-8364-55a513462b80" />
 
# Parte 2
## Descripción del proyecto
Para la segunda parte de esta práctica, se utilizó la KL25Z para crear un sistema con múltiples interrupciones desde un mismo puerto junto con un display LCD, en donde se detectan dos botones diferentes (PTA1 y PTA13) y se muestra en pantalla cuál fue presionado. El funcionamiento de este código incluye la inicialización del LCD en modo de 4 bits, el uso de interrupciones para identificar cada botón y desplegar mensajes como “Boton PTA1” o “Boton PTA13”, mientras que el LED rojo continúa parpadeando en el ciclo principal hasta que ocurre alguna interrupción.

## Diagrama de flujo

## Esquematico
<img width="524" height="407" alt="practica4_pt2_esquematico" src="https://github.com/user-attachments/assets/d693dbda-9129-4e32-bfce-6e3e417d381a" />


## Funcionamiento
Fotos del funcionamiento del ejericicio 2:
<div align="center">
 <img width="1600" height="900" alt="Practica4_img1" src="https://github.com/user-attachments/assets/97dae52c-1c11-489e-91b2-1b1c07ebca32" 
  />
 <img width="1600" height="900" alt="Practica4_img2" src="https://github.com/user-attachments/assets/2bb63685-a385-4205-ba86-3f1230e48dfd" 
  />
 <img width="1600" height="900" alt="Practica4_img3" src="https://github.com/user-attachments/assets/7c8cd3dc-83c9-45d3-9a93-c433860c594f" 
  />
</div>

# Parte 3
## Descripción del proyecto
Para la tercera parte de esta práctica, se utilizó la KL25Z para crear un sistema más completo que integra teclado matricial, display LCD, temporizador e interrupciones, en donde el usuario ingresa un tiempo en segundos y el sistema realiza un conteo hasta alcanzar ese valor. El funcionamiento de este código incluye la lectura de datos desde el keypad, la configuración del TPM0 para generar intervalos de 1 segundo y una interrupción en PTA1 que permite pausar el conteo mostrando “PAUSED” en el LCD, el cual puede reanudarse al presionar “*”; al finalizar el tiempo, se muestra “Tiempo cumplido!” y el LED parpadea antes de indicar el fin del programa.

## Diagrama de flujo


## Funcionamiento
Fotos del funcionamiento del ejericicio 3

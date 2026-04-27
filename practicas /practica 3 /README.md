#### Miguel Alonso De La Rosa Zamora A01646106
#### Gregorio Alejandro Orozco Torres A01641967
#### A01639462 Sophia Leñero Gómez

# Práctica 3 - LCD-Keyboard-Timers

# Parte 1
## Descripción de la práctica
Para la primera parte de esta práctica, teníamos que usar la KL25Z para crear un sistema con un display LCD y el LED de la tarjeta, en dónde sólo podíamos escoger entre las opciones de 1 - prendiendo el LED rojo, 2 - prendiendo el LED azul o 3 - prendiendo el LED verde. 
El funcionamiento de esto inclye una función capaz de recuperar los datos de get_key() y la tecla presionada, mostrando además un RED/BLUE/GREEN LED IS ON! Tras esto, el LED se queda encendido por algunos segunods hasta eventualmente apagarse. 

## Diagrama de flujo
<div align="center">
 <img width=50% height="996" alt="image" src="https://github.com/user-attachments/assets/f2f5bf94-672c-4b92-8abd-e2ce2e940e93" />
</div>

## Esquemático del circuito utilizado 
<div align="center">
 <img width="524" height="407" alt="image" src="https://github.com/user-attachments/assets/4c8084cf-5f77-46f4-9c64-c9f24b9d2b0b" />
</div>

## Funcionamiento
Gracias a una integración de la parte de hardware y software, se pudo comprobar que el sistema funciona de manera efectiva, dejando escoger al usuario entre LEDs y cumpliendo de manera adecuada con las interrupciones
Fotografías del sistema funcionando: 
<div align="center">
 <img width=30% height=30% alt="image" src="https://github.com/user-attachments/assets/c1130f10-3dbb-4579-9a9b-44737ae8a0fd" />
 <img width=30% height=30% alt="image" src="https://github.com/user-attachments/assets/43976d99-d44d-4eac-8814-652332004056" />
 <img width=30% height=30% alt="image" src="https://github.com/user-attachments/assets/15fb9f5c-d606-48ef-8691-0b8a23ac6120" />
</div>

# Parte 2
## Descripción de la práctica
Para la segunda parte de esta práctica, se utilizó la KL25Z para crear un temporizador ascendente con apoyo de un display LCD y el teclado matricial, en donde primero se captura la cantidad de segundos que desea ingresar el usuario y después el sistema comienza a contar de forma automática hasta llegar al límite establecido. El funcionamiento de este código incluye una función para configurar el TPM0 con un periodo de 1 segundo, otra para leer los segundos tecleados y mostrarlos en el LCD, y al finalizar el conteo se despliega el mensaje de “Tiempo cumplido!”, haciendo parpadear el LED de la tarjeta antes de dejar el programa detenido.

## Diagrama de flujo

## Funcionamiento 
[![Ver video](https://img.youtube.com/vi/RXWTv0RfCsw/0.jpg)](https://youtube.com/shorts/RXWTv0RfCsw)

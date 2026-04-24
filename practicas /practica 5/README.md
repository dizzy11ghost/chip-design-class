#### Miguel Alonso De La Rosa Zamora A01646106
#### Gregorio Alejandro Orozco Torres A01641967
#### A01639462 Sophia Leñero Gómez

# Práctica 5 - Protocolo de comunicación UART 

## Descripción del proyecto
 Para esta práctica, había dos partes importantes, la primera consistía en utilizar un potenciometro, un display LCD y una KL25z para hacer nuestro propio voltimetro, capaz de detectar y mostrar en el display los cambios en el voltaje al mover el potenciómetro. La segunda parte de la práctica consistía en simular un sistema médico en el que al detectar una temperatura corporal elevada, se encendiera un ventilador. A falta de ciertos materiales, se propuso realizar un prorotipo utilizando una fotoresistencia, un display LCD, una KL25z y el LED RGB de esta. 
 
## Funcionamiento
# Diagrama de funcionamiento parte 1
<img width="365" height="886" alt="image" src="https://github.com/user-attachments/assets/5815c0be-10cd-447c-8682-8d6da5a974a5" />
<img width="524" height="407" alt="image" src="https://github.com/user-attachments/assets/66111edf-3194-4874-b5d4-be6ad954b520" />


El programa lee la señal analógica de un potenciómetro conectado al pin PTE2o de la KL25z por medio del convertidor ADC. El valor se convierte a un voltaje equivantente entre 0 y 3.3 V y se va mostrando continuamente en una pantalla LCD. 

# Diagrama de funcionamiento parte 2 
<img width="605" height="789" alt="image" src="https://github.com/user-attachments/assets/03d58aec-c48f-4a9a-9f33-4c82aedc8a8f" />
<img width="524" height="407" alt="image" src="https://github.com/user-attachments/assets/f3ecabe0-491c-4730-a70a-2f9c4ea26175" />

Este programa utiliza una fotoresistencia continuamente leída usando el convertidor ADC, y el valor obtenido es pasado a un porcentaje de intensidad luminosa. L información se muestra en un display LCD, indicando el nivel de luz y el estado del sistema, esto dependiendo de si la ilumniación pasa o no de el umbral establecidp del 75%. Aparte, dependiendo del umbral, un LED se enciende para representar si la luz detectada es baja o suficiente. 






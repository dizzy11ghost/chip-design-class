#### Miguel Alonso De La Rosa Zamora A01646106
#### Gregorio Alejandro Orozco Torres A01641967
#### A01639462 Sophia Leñero Gómez

# Práctica 6 - Protocolo de comunicación UART 

## Descripción del proyecto
 Para esta práctica, había dos partes importantes, la primera consistía en utilizar un potenciometro, un display LCD y una KL25z para hacer nuestro propio voltimetro, capaz de detectar y mostrar en el display los cambios en el voltaje al mover el potenciómetro. La segunda parte de la práctica consistía en simular un sistema médico en el que al detectar una temperatura corporal elevada, se encendiera un ventilador. A falta de ciertos materiales, se propuso realizar un prorotipo utilizando una fotoresistencia, un display LCD, una KL25z y el LED RGB de esta. 
 
## Funcionamiento
# Diagrama de funcionamiento 
<img width="365" height="886" alt="image" src="https://github.com/user-attachments/assets/5815c0be-10cd-447c-8682-8d6da5a974a5" />

El programa lee la señal analógica de un potenciómetro conectado al pin PTE2o de la KL25z por medio del convertidor ADC. El valor se convierte a un voltaje equivantente entre 0 y 3.3 V y se va mostrando continuamente en una pantalla LCD. 




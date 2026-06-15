Miguel Alonso De La Rosa Zamora A01646106 - Gregorio Alejandro Orozco Torres A01641967 - Sophia Leñero Gómez A01639462

# Practica2-ADC+GPIO+LEDs

## Descripción de la práctica
Diseñar e implementación de un sistema embebido multitarea utilizando el sistema operativo de tiempo real FreeRTOS sobre la tarjeta de desarrollo FRDM-KL25Z. Desarrollamos un sistema de monitoreo para las señales analógicas de los dos potenciómetros y un boton para controlar el estado del LED RGB integrado en la KL25. El proyecto va evolucionando en cada fase por partes de su arquitectura con variables globales sin control de concurrencia, al igual que la estructura de los queues, hasta la solución robusta con la implementacion del Mutex que busca eliminar las colisiones en el ADC0.

## Stage 1
En esta etapa se configuraron las tareas para ue se comunicaran usando variables globales directamente en la memoria. El problema principal fue que el sistema operó sin control de concurrencia y eso provoco condiciones de carrera al estar todas las tareas compitiendo por el tiempo del CPU. Se modificaban los mismos espacios de memoria al mismo tiempo, lo que provoco que no funionaran bien los datos y las lecturas por lo que se aprecia en el video de la practica como se quedo atorada leyendo solo el sensor de luz mientras que ignoraba las lecturas de los demas sensores para activar el led.

## Stage 2
En la segunda fase se eliminaron las variables globales y se implementó el queue de FreeRTOS. Aunque ahora el sistema si reacciono ante las lecturas de tosos los sensores, el sistema falló debido a la colisión de hardware en donde las dos tareas de adquisición analógica intentaron acceder al mismo tiempo al registro del único periférico ADC0 de la tarjeta. Al no haber exclusión mutua, esto provoco que el hardware se quedara leyendo solo al sensor de luz, dejando congelado de forma permanente el LED rojo del sensor de temperatura.

## Stage 3
En la ultima fase se introdujo el Mutex al codigo para proteger las señales mandadas por los periféricos analógicos. Esto obligo a que las tareas de luz y temperatura pudieran acceder al ADC0 por turnos antes de iniciar una conversión y a liberarla inmediatamente al terminar. Tambien se optimización el botón mediante un polling y se eliminaron por completo los bloqueos de hardware, logrando que todos los sensores y LEDs funcionaran simultáneamente en tiempo real y con un funcionamiento estable. Ademas tambien se puede observar como tienen una responsividad rapida y que no se confunden las tareas al accionarse simultaneamente.

# Funcionamiento
## Stage 1
[![Ver video](https://img.youtube.com/vi/Uz_tZ-qPJtY/hqdefault.jpg)](https://youtu.be/Uz_tZ-qPJtY)

## Stage 2
[![Ver video](https://img.youtube.com/vi/UhbtA1tAiog/hqdefault.jpg)](https://youtu.be/UhbtA1tAiog)

## Stage 3
[![Ver video](https://img.youtube.com/vi/VKhde_QbSjU/hqdefault.jpg)](https://youtu.be/VKhde_QbSjU)

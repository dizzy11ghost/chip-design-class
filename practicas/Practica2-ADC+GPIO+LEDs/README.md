Miguel Alonso De La Rosa Zamora A01646106 - Gregorio Alejandro Orozco Torres A01641967 - Sophia Leñero Gómez A01639462

# Practica2-ADC+GPIO+LEDs

## Descripción de la práctica
Diseñar e implementación de un sistema embebido multitarea utilizando el sistema operativo de tiempo real FreeRTOS sobre la tarjeta de desarrollo FRDM-KL25Z. Desarrollamos un sistema de monitoreo para las señales analógicas de los dos potenciómetros y un boton para controlar el estado del LED RGB integrado en la KL25. El proyecto va evolucionando en cada fase por partes de su arquitectura con variables globales sin control de concurrencia, al igual que la estructura de los queues, hasta la solución robusta con la implementacion del Mutex que busca eliminar las colisiones en el ADC0.

## Stage 1
El uso de variables globales nos permitió poder implementar de manera más veloz y sencilla el que las tareas compartieran información, sin embargo, hay varios defectos en este enfoque... Las tareas tienen que estar constantemente realizando polling para verificar qué cambios se han hecho, desperdiciando así tiempo de CPU y haciendo el sistema menos eficiente.
Además esta el hecho de que las variables globales generan riesgos de race conditions, ya que múltiples tareas pueden tener acceso al mismo tiempo a los mismos datos sin ningun tipo de protección, limitante o control.
El sistema funciona bien en este caso, ya que es una aplicación pequeña, pero si tuvieramos que escalarlo, este diseño probablemente no serviría, ya que hay muchos recursos desperdiciados y en caso de escalarlo mucho las variables globales se volverían imposibles de controlar.

## Stage 2
Primero que nada, recordando que es una queue... Una queue es una estructura de datos LIFO (last in first out) en la que las tareas productoras pueden meter mensajes y otras tareas pueden esperar mensajes de dicha queue. 
Usar este tipo de estructuras nos permite evitar que el CPU se active sin razón, eliminando en gran parte los riesgos de race condition. Aparte, al no tener variables globales compartidas, la comunicación se vuelve más segura. Además, cada tarea es independiente, por lo que el código se puede ver como que esta separado en diferentes modulos, y se vuelve más fácil debuggearlo, darle mantenimiento y escalarlo. 

## Stage 3
Primero que nada, recordando que es una queue... Una queue es una estructura de datos LIFO (last in first out) en la que las tareas productoras pueden meter mensajes y otras tareas pueden esperar mensajes de dicha queue. 
Usar este tipo de estructuras nos permite evitar que el CPU se active sin razón, eliminando en gran parte los riesgos de race condition. Aparte, al no tener variables globales compartidas, la comunicación se vuelve más segura. Además, cada tarea es independiente, por lo que el código se puede ver como que esta separado en diferentes modulos, y se vuelve más fácil debuggearlo, darle mantenimiento y escalarlo. 

# Funcionamiento
## Stage 1
[![Ver video](https://img.youtube.com/vi/Uz_tZ-qPJtY/hqdefault.jpg)](https://youtu.be/Uz_tZ-qPJtY)

## Stage 2
[![Ver video](https://img.youtube.com/vi/UhbtA1tAiog/hqdefault.jpg)](https://youtu.be/UhbtA1tAiog)

## Stage 3
[![Ver video](https://img.youtube.com/vi/VKhde_QbSjU/hqdefault.jpg)](https://youtu.be/VKhde_QbSjU)

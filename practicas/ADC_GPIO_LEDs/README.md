Miguel Alonso De La Rosa Zamora A01646106 - Gregorio Alejandro Orozco Torres A01641967 - Sophia Leñero Gómez A01639462

# Práctica ADC+GPIO+LEDs con FreeRTOS

## Descripción de la práctica
Para esta práctica, teníamos que utilizar una tarjeta KL25z para implementar un sistema con FreeRTOS capaz de discernir entre prioridades de lecturas de dos potenciometros simulando un sensor de luz y un sensor de temperatura. 

## Reflexión variables globales
El uso de variables globales nos permitió poder implementar de manera más veloz y sencilla el que las tareas compartieran información, sin embargo, hay varios defectos en este enfoque... Las tareas tienen que estar constantemente realizando polling para verificar qué cambios se han hecho, desperdiciando así tiempo de CPU y haciendo el sistema menos eficiente.
Además esta el hecho de que las variables globales generan riesgos de race conditions, ya que múltiples tareas pueden tener acceso al mismo tiempo a los mismos datos sin ningun tipo de protección, limitante o control.
El sistema funciona bien en este caso, ya que es una aplicación pequeña, pero si tuvieramos que escalarlo, este diseño probablemente no serviría, ya que hay muchos recursos desperdiciados y en caso de escalarlo mucho las variables globales se volverían imposibles de controlar.

## Ventajas de utilizar Queues
Primero que nada, recordando que es una queue... Una queue es una estructura de datos LIFO (last in first out) en la que las tareas productoras pueden meter mensajes y otras tareas pueden esperar mensajes de dicha queue. 
Usar este tipo de estructuras nos permite evitar que el CPU se active sin razón, eliminando en gran parte los riesgos de race condition. Aparte, al no tener variables globales compartidas, la comunicación se vuelve más segura. Además, cada tarea es independiente, por lo que el código se puede ver como que esta separado en diferentes modulos, y se vuelve más fácil debuggearlo, darle mantenimiento y escalarlo. 



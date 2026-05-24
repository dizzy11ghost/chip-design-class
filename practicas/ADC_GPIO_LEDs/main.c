// Práctica 1. FreeRTOS ADC + GPIO + LEDs
#include <stdio.h>
#include "board.h"
#include "peripherals.h"
#include "pin_mux.h"
#include "clock_config.h"
#include "fsl_debug_console.h"
/* FreeRTOS kernel includes. */
#include "FreeRTOS.h"
#include "task.h"
#include "queue.h"
#include "timers.h"
/* Freescale includes. */
#include "fsl_device_registers.h"
#include "fsl_debug_console.h"
#include "board.h"

// Declaración de tareas
void vTaskBoton( void *pvParameters );

int main(void) {
    /* Init board hardware. */
    BOARD_InitBootPins();
    BOARD_InitBootClocks();
    BOARD_InitBootPeripherals();

    // Definición de tareas
    xTaskCreate(vTaskBoton, "Tarea Boton", 1000, NULL, 1, NULL);
    // Inciamos las tareas
    vTaskStartScheduler();
    for (;;);
}

void vTaskBoton( void *pvParameters )
{
    for( ;; )
    {
        if( (PTB->PDIR & (1 << 0)) == 0 ){
        	PRINTF("Botón presionado\r\n");
            LED_GREEN_ON();
        }
        else
            LED_GREEN_OFF();
        vTaskDelay( pdMS_TO_TICKS(10) );
    }
}

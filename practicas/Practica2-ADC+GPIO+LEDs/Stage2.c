#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include "FreeRTOS.h"
#include "task.h"
#include "queue.h" // ¡Nueva librería para el manejo de colas!
#include "board.h"
#include "pin_mux.h"
#include "clock_config.h"
#include "fsl_debug_console.h"
#include "fsl_gpio.h"
#include "fsl_adc16.h"
#include "fsl_port.h"

// ============================================================================
// ESTRUCTURAS Y ENUMS (Nuevos para Fase 2)
// ============================================================================

// Enumeración para identificar el origen del dato
typedef enum {
    SOURCE_LIGHT,
    SOURCE_TEMPERATURE,
    SOURCE_BUTTON
} sensor_source_t;

// Estructura estandarizada para el paquete de datos (Mensaje)
typedef struct {
    sensor_source_t source; // Quién envía el dato
    uint16_t value;         // El valor del dato leído
} sensor_msg_t;

// ============================================================================
// CONFIGURACIÓN DE HARDWARE Y CONSTANTES
// ============================================================================
#define BUTTON_PORT GPIOB
#define BUTTON_GPIO PORTB
#define BUTTON_PIN 0U

#define ADC_BASE ADC0
#define ADC_CH_LIGHT 9U       // PTB1
#define ADC_CH_TEMPERATURE 12U // PTB2

#define LIGHT_THRESHOLD 2048
#define TEMP_THRESHOLD 2048

#define QUEUE_LENGTH 10 // Capacidad máxima de la cola (10 mensajes)

// Handler de la cola global
QueueHandle_t sensorQueue = NULL;

// Prototipos de Funciones (Se desactiva Serial Monitor en esta fase)
static void vTaskLightSensor(void *pvParameters);
static void vTaskTemperatureSensor(void *pvParameters);
static void vTaskButtonPolling(void *pvParameters);
static void vTaskLedControl(void *pvParameters);

// ============================================================================
// FUNCIÓN PRINCIPAL (MAIN)
// ============================================================================
int main(void) {
    BOARD_InitBootPins();
    BOARD_InitBootClocks();
    BOARD_InitDebugConsole();

    CLOCK_EnableClock(kCLOCK_PortB);
    
    PORT_SetPinMux(BUTTON_GPIO, BUTTON_PIN, kPORT_MuxAsGpio);
    BUTTON_GPIO->PCR[BUTTON_PIN] |= PORT_PCR_PE_MASK | PORT_PCR_PS_MASK;

    gpio_pin_config_t button_gpio_config = { kGPIO_DigitalInput, 0 };
    GPIO_PinInit(BUTTON_PORT, BUTTON_PIN, &button_gpio_config);

    adc16_config_t adc16ConfigStruct;
    ADC16_GetDefaultConfig(&adc16ConfigStruct);
    adc16ConfigStruct.resolution = kADC16_ResolutionSE12Bit;
    adc16ConfigStruct.enableContinuousConversion = false;
    ADC16_Init(ADC_BASE, &adc16ConfigStruct);
    ADC16_EnableHardwareTrigger(ADC_BASE, false);
    ADC16_DoAutoCalibration(ADC_BASE);

    PRINTF("--- FreeRTOS FRDM-KL25Z: Fase 2 (Message Queues) ---\r\n");

    // 1. Creación de la cola de mensajes
    sensorQueue = xQueueCreate(QUEUE_LENGTH, sizeof(sensor_msg_t));

    if (sensorQueue != NULL) {
        // 2. Creación de Tareas (Se removió la tarea de Serial Monitor)
        xTaskCreate(vTaskLightSensor, "Light", configMINIMAL_STACK_SIZE + 100, NULL, 2, NULL);
        xTaskCreate(vTaskTemperatureSensor, "Temp", configMINIMAL_STACK_SIZE + 100, NULL, 2, NULL);
        xTaskCreate(vTaskButtonPolling, "Button", configMINIMAL_STACK_SIZE + 100, NULL, 1, NULL);
        xTaskCreate(vTaskLedControl, "LEDs", configMINIMAL_STACK_SIZE + 100, NULL, 3, NULL);

        // Arrancar el Planificador
        vTaskStartScheduler();
    } else {
        PRINTF("Error crítico: No se pudo crear la cola de mensajes.\r\n");
    }

    while(1) {}
}

// ============================================================================
// IMPLEMENTACIÓN DE TAREAS (PRODUCTORES)
// ============================================================================

static void vTaskLightSensor(void *pvParameters)
{
    adc16_channel_config_t adcConfigLight;
    adcConfigLight.channelNumber = ADC_CH_LIGHT;
    adcConfigLight.enableInterruptOnConversionCompleted = false;
    adcConfigLight.enableDifferentialConversion = false;
    
    sensor_msg_t msg;
    msg.source = SOURCE_LIGHT;

    while(1)
    {
        // NOTA DE FALLO HARDWARE: Sigue existiendo riesgo de colisión en ADC_BASE (Sin Mutex aún)
        ADC16_SetChannelConfig(ADC_BASE, 0U, &adcConfigLight);
        while (0U == (kADC16_ChannelConversionDoneFlag & ADC16_GetChannelStatusFlags(ADC_BASE, 0U))) {}
        msg.value = ADC16_GetChannelConversionValue(ADC_BASE, 0U);
        
        // Envío seguro a la cola. Si está llena, espera 0 ticks (descarta el dato antiguo)
        xQueueSend(sensorQueue, &msg, 0U);
        
        vTaskDelay(pdMS_TO_TICKS(500));
    }
}

static void vTaskTemperatureSensor(void *pvParameters)
{
    adc16_channel_config_t adcConfigTemperature;
    adcConfigTemperature.channelNumber = ADC_CH_TEMPERATURE;
    adcConfigTemperature.enableInterruptOnConversionCompleted = false;
    adcConfigTemperature.enableDifferentialConversion = false;
    
    sensor_msg_t msg;
    msg.source = SOURCE_TEMPERATURE;

    while(1)
    {
        // NOTA DE FALLO HARDWARE: Sigue existiendo riesgo de colisión en ADC_BASE
        ADC16_SetChannelConfig(ADC_BASE, 0U, &adcConfigTemperature);
        while (0U == (kADC16_ChannelConversionDoneFlag & ADC16_GetChannelStatusFlags(ADC_BASE, 0U))) {}
        msg.value = ADC16_GetChannelConversionValue(ADC_BASE, 0U);
        
        xQueueSend(sensorQueue, &msg, 0U);
        
        vTaskDelay(pdMS_TO_TICKS(500));
    }
}

static void vTaskButtonPolling(void *pvParameters)
{
    sensor_msg_t msg;
    msg.source = SOURCE_BUTTON;
    uint32_t last_state = 0;

    for (;;) {
        uint32_t current_state = !GPIO_ReadPinInput(BUTTON_PORT, BUTTON_PIN);

        // Solo enviamos mensaje si hay un cambio de estado detectado (Optimización de tráfico en la cola)
        if (current_state != last_state) {
            msg.value = current_state;
            xQueueSend(sensorQueue, &msg, 0U);
            last_state = current_state;
        }

        vTaskDelay(pdMS_TO_TICKS(50));
    }
}

// ============================================================================
// IMPLEMENTACIÓN DE TAREA (CONSUMIDOR)
// ============================================================================

static void vTaskLedControl(void *pvParameters)
{
    sensor_msg_t received_msg;

    while(1)
    {
        /*
          EFICIENCIA TOTAL: La tarea entra en estado "Blocked" indefinidamente (portMAX_DELAY).
          No consume ciclos de CPU hasta que xQueueReceive detecte un nuevo paquete en la cola.
        */
        if (xQueueReceive(sensorQueue, &received_msg, portMAX_DELAY) == pdPASS) {
            
            // Evaluamos según quién envió el mensaje
            switch (received_msg.source) {
                case SOURCE_LIGHT:
                    if (received_msg.value < LIGHT_THRESHOLD) {
                        LED_BLUE_ON();
                    } else {
                        LED_BLUE_OFF();
                    }
                    break;

                case SOURCE_TEMPERATURE:
                    if (received_msg.value > TEMP_THRESHOLD) {
                        LED_RED_ON();
                    } else {
                        LED_RED_OFF();
                    }
                    break;

                case SOURCE_BUTTON:
                    if (received_msg.value == 1) {
                        LED_GREEN_ON();
                    } else {
                        LED_GREEN_OFF();
                    }
                    break;
                
                default:
                    break;
            }
        }
    }
}

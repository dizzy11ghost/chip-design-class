#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include "FreeRTOS.h"
#include "task.h"
#include "queue.h"
#include "semphr.h"
#include "board.h"
#include "pin_mux.h"
#include "clock_config.h"
#include "fsl_debug_console.h"
#include "fsl_gpio.h"
#include "fsl_adc16.h"
#include "fsl_port.h"

// ============================================================================
// ESTRUCTURAS Y ENUMS
// ============================================================================
typedef enum {
    SOURCE_LIGHT,
    SOURCE_TEMPERATURE,
    SOURCE_BUTTON
} sensor_source_t;

typedef struct {
    sensor_source_t source;
    uint16_t value;
} sensor_msg_t;

// ============================================================================
// CONFIGURACIÓN DE HARDWARE
// ============================================================================
#define BUTTON_PORT GPIOB
#define BUTTON_GPIO PORTB
#define BUTTON_PIN 0U

// CORRECCIÓN VECTOR: En el KL25Z, las interrupciones del puerto B se direccionan mediante PORTA_IRQn
#define BUTTON_IRQ PORTA_IRQn          

#define ADC_BASE ADC0
#define ADC_CH_LIGHT 9U       // PTB1
#define ADC_CH_TEMPERATURE 12U // PTB2

#define LIGHT_THRESHOLD 2048
#define TEMP_THRESHOLD 2048
#define QUEUE_LENGTH 10

// ============================================================================
// HANDLERS DE FREERTOS
// ============================================================================
QueueHandle_t sensorQueue = NULL;
SemaphoreHandle_t xAdcMutex = NULL;
SemaphoreHandle_t xButtonSemaphore = NULL;

// Prototipos de Funciones
static void vTaskLightSensor(void *pvParameters);
static void vTaskTemperatureSensor(void *pvParameters);
static void vTaskButtonInterruptHandler(void *pvParameters);
static void vTaskLedControl(void *pvParameters);

// ============================================================================
// FUNCIÓN PRINCIPAL (MAIN)
// ============================================================================
int main(void) {
    BOARD_InitBootPins();
    BOARD_InitBootClocks();
    BOARD_InitDebugConsole();

    CLOCK_EnableClock(kCLOCK_PortB);
    
    // Configurar PTB0 con resistencia de Pull-Up interna e Interrupción por Flanco de Bajada
    PORT_SetPinMux(BUTTON_GPIO, BUTTON_PIN, kPORT_MuxAsGpio);
    BUTTON_GPIO->PCR[BUTTON_PIN] |= PORT_PCR_PE_MASK | PORT_PCR_PS_MASK | PORT_PCR_IRQC(0x0AU);

    gpio_pin_config_t button_gpio_config = { kGPIO_DigitalInput, 0 };
    GPIO_PinInit(BUTTON_PORT, BUTTON_PIN, &button_gpio_config);

    // Configurar prioridad de la interrupción en el NVIC y habilitarla
    NVIC_SetPriority(BUTTON_IRQ, 2);
    EnableIRQ(BUTTON_IRQ);

    // Inicialización del Periférico ADC0
    adc16_config_t adc16ConfigStruct;
    ADC16_GetDefaultConfig(&adc16ConfigStruct);
    adc16ConfigStruct.resolution = kADC16_ResolutionSE12Bit;
    adc16ConfigStruct.enableContinuousConversion = false;
    ADC16_Init(ADC_BASE, &adc16ConfigStruct);
    ADC16_EnableHardwareTrigger(ADC_BASE, false);
    ADC16_DoAutoCalibration(ADC_BASE);

    PRINTF("--- FreeRTOS FRDM-KL25Z: Fase 3 Final Funcionando ---\r\n");

    // Creación de recursos de FreeRTOS
    sensorQueue = xQueueCreate(QUEUE_LENGTH, sizeof(sensor_msg_t));
    xAdcMutex = xSemaphoreCreateMutex();
    xButtonSemaphore = xSemaphoreCreateBinary();

    if ((sensorQueue != NULL) && (xAdcMutex != NULL) && (xButtonSemaphore != NULL)) {
        
        xTaskCreate(vTaskLightSensor, "Light", configMINIMAL_STACK_SIZE + 100, NULL, 2, NULL);
        xTaskCreate(vTaskTemperatureSensor, "Temp", configMINIMAL_STACK_SIZE + 100, NULL, 2, NULL);
        xTaskCreate(vTaskButtonInterruptHandler, "Button", configMINIMAL_STACK_SIZE + 100, NULL, 1, NULL);
        xTaskCreate(vTaskLedControl, "LEDs", configMINIMAL_STACK_SIZE + 100, NULL, 3, NULL);

        vTaskStartScheduler();
    } else {
        PRINTF("Error crítico: No se pudieron crear los recursos.\r\n");
    }

    while(1) {}
}

// ============================================================================
// RUTINA DE SERVICIO DE INTERRUPCIÓN (ISR)
// ============================================================================
// Manejador unificado de interrupciones de puertos para el KL25Z
void PORTA_IRQHandler(void) {
    BaseType_t xHigherPriorityTaskWoken = pdFALSE;

    // Limpiar banderas del puerto B (donde está nuestro botón PTB0)
    uint32_t flags = GPIO_GetPinsInterruptFlags(BUTTON_PORT);
    GPIO_ClearPinsInterruptFlags(BUTTON_PORT, flags);

    // Despertar la tarea del botón enviando el semáforo binario
    xSemaphoreGiveFromISR(xButtonSemaphore, &xHigherPriorityTaskWoken);

    // Forzar el cambio de contexto inmediato si corresponde
    portYIELD_FROM_ISR(xHigherPriorityTaskWoken);
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
        if (xSemaphoreTake(xAdcMutex, portMAX_DELAY) == pdTRUE) {
            ADC16_SetChannelConfig(ADC_BASE, 0U, &adcConfigLight);
            while (0U == (kADC16_ChannelConversionDoneFlag & ADC16_GetChannelStatusFlags(ADC_BASE, 0U))) {}
            msg.value = ADC16_GetChannelConversionValue(ADC_BASE, 0U);
            xSemaphoreGive(xAdcMutex);
            
            xQueueSend(sensorQueue, &msg, 0U);
        }
        vTaskDelay(pdMS_TO_TICKS(250)); // Reducido a 250ms para mayor fluidez visual
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
        if (xSemaphoreTake(xAdcMutex, portMAX_DELAY) == pdTRUE) {
            ADC16_SetChannelConfig(ADC_BASE, 0U, &adcConfigTemperature);
            while (0U == (kADC16_ChannelConversionDoneFlag & ADC16_GetChannelStatusFlags(ADC_BASE, 0U))) {}
            msg.value = ADC16_GetChannelConversionValue(ADC_BASE, 0U);
            xSemaphoreGive(xAdcMutex);
            
            xQueueSend(sensorQueue, &msg, 0U);
        }
        vTaskDelay(pdMS_TO_TICKS(250)); // Reducido a 250ms para mayor fluidez visual
    }
}

static void vTaskButtonInterruptHandler(void *pvParameters)
{
    sensor_msg_t msg;
    msg.source = SOURCE_BUTTON;
    uint32_t last_stable_state = 0;

    for (;;) {
        // Bloqueado al 0% de CPU hasta que ocurra la interrupción física del botón
        if (xSemaphoreTake(xButtonSemaphore, portMAX_DELAY) == pdTRUE) {
            
            vTaskDelay(pdMS_TO_TICKS(50)); // Filtro Debounce para ruido mecánico
            
            uint32_t current_state = !GPIO_ReadPinInput(BUTTON_PORT, BUTTON_PIN);
            
            if (current_state != last_stable_state) {
                msg.value = current_state;
                xQueueSend(sensorQueue, &msg, 0U);
                last_stable_state = current_state;
            }
            
            xSemaphoreTake(xButtonSemaphore, 0U); // Vaciar rebotes fantasmas de la cola
        }
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
        if (xQueueReceive(sensorQueue, &received_msg, portMAX_DELAY) == pdPASS) {
            switch (received_msg.source) {
                case SOURCE_LIGHT:
                    // Luz: Si baja del umbral (oscuridad) prende Azul, de lo contrario apaga
                    if (received_msg.value < LIGHT_THRESHOLD) {
                        LED_BLUE_ON();
                    } else {
                        LED_BLUE_OFF();
                    }
                    break;

                case SOURCE_TEMPERATURE:
                    // CORRECCIÓN LOGICA INVERSA: Cambiado '>' por '<' para alinearse al giro del potenciómetro
                    if (received_msg.value < TEMP_THRESHOLD) {
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
            }
        }
    }
}

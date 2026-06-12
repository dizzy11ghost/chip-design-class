#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include "FreeRTOS.h"
#include "task.h"
#include "board.h"
#include "pin_mux.h"
#include "clock_config.h"
#include "fsl_debug_console.h"
#include "fsl_gpio.h"
#include "fsl_adc16.h"
#include "fsl_port.h"

// Variables globales protegidas por "volatile" (Anti-patrón didáctico)
volatile uint16_t light_value = 0;
volatile uint16_t temp_value = 0;
volatile uint16_t button_state = 0;

// Definiciones de Hardware para FRDM-KL25Z
#define BUTTON_PORT GPIOB
#define BUTTON_GPIO PORTB
#define BUTTON_PIN 0U      // PTB0

#define ADC_BASE ADC0
#define ADC_CH_LIGHT 9U       // PTB1 (ADC0_SE9)
#define ADC_CH_TEMPERATURE 12U // PTB2 (ADC0_SE12)

#define LIGHT_THRESHOLD 2048
#define TEMP_THRESHOLD 2048

// Prototipos de Funciones
static void vTaskLightSensor(void *pvParameters);
static void vTaskTemperatureSensor(void *pvParameters);
static void vTaskButtonPolling(void *pvParameters);
static void vTaskLedControl(void *pvParameters);
static void vTaskSerialMonitor(void *pvParameters);

int main(void) {
    // Inicialización del sistema base de la tarjeta
    BOARD_InitBootPins();
    BOARD_InitBootClocks();
    BOARD_InitDebugConsole();

    // Configuración del Reloj para el Puerto B (Botón y Canales ADC)
    CLOCK_EnableClock(kCLOCK_PortB);
    
    // Configurar PTB0 como GPIO con resistencia de Pull-Up interna
    PORT_SetPinMux(BUTTON_GPIO, BUTTON_PIN, kPORT_MuxAsGpio);
    BUTTON_GPIO->PCR[BUTTON_PIN] |= PORT_PCR_PE_MASK | PORT_PCR_PS_MASK;

    gpio_pin_config_t button_gpio_config = {
        kGPIO_DigitalInput,
        0
    };
    GPIO_PinInit(BUTTON_PORT, BUTTON_PIN, &button_gpio_config);

    // Inicialización del Periférico ADC0
    adc16_config_t adc16ConfigStruct;
    ADC16_GetDefaultConfig(&adc16ConfigStruct);
    adc16ConfigStruct.resolution = kADC16_ResolutionSE12Bit;
    adc16ConfigStruct.enableContinuousConversion = false;
    ADC16_Init(ADC_BASE, &adc16ConfigStruct);
    ADC16_EnableHardwareTrigger(ADC_BASE, false);
    ADC16_DoAutoCalibration(ADC_BASE);

    PRINTF("--- FreeRTOS FRDM-KL25Z: Fase 1 (Polling y Globales) ---\r\n");

    // Creación de Tareas con sus respectivas prioridades de la práctica
    xTaskCreate(vTaskLightSensor, "Light", configMINIMAL_STACK_SIZE + 100, NULL, 2, NULL);
    xTaskCreate(vTaskTemperatureSensor, "Temp", configMINIMAL_STACK_SIZE + 100, NULL, 2, NULL);
    xTaskCreate(vTaskButtonPolling, "Button", configMINIMAL_STACK_SIZE + 100, NULL, 1, NULL);
    xTaskCreate(vTaskLedControl, "LEDs", configMINIMAL_STACK_SIZE + 100, NULL, 3, NULL);
    xTaskCreate(vTaskSerialMonitor, "Serial", configMINIMAL_STACK_SIZE + 200, NULL, 1, NULL);

    // Arrancar el Planificador (Scheduler)
    vTaskStartScheduler();

    while(1) {}
}

static void vTaskLightSensor(void *pvParameters)
{
    adc16_channel_config_t adcConfigLight;
    adcConfigLight.channelNumber = ADC_CH_LIGHT;
    adcConfigLight.enableInterruptOnConversionCompleted = false;
    adcConfigLight.enableDifferentialConversion = false;

    while(1)
    {
        // NOTA DE FALLO: Ambas tareas ADC comparten el mismo canal de hardware (ADC_BASE) sin protección.
        ADC16_SetChannelConfig(ADC_BASE, 0U, &adcConfigLight);
        while (0U == (kADC16_ChannelConversionDoneFlag & ADC16_GetChannelStatusFlags(ADC_BASE, 0U))) {}
        light_value = ADC16_GetChannelConversionValue(ADC_BASE, 0U);
        
        vTaskDelay(pdMS_TO_TICKS(500));
    }
}

static void vTaskTemperatureSensor(void *pvParameters)
{
    adc16_channel_config_t adcConfigTemperature;
    adcConfigTemperature.channelNumber = ADC_CH_TEMPERATURE;
    adcConfigTemperature.enableInterruptOnConversionCompleted = false;
    adcConfigTemperature.enableDifferentialConversion = false;

    while(1)
    {
        // NOTA DE FALLO: Si esta tarea interrumpe a la de Luz aquí, causará una colisión de registros ADC.
        ADC16_SetChannelConfig(ADC_BASE, 0U, &adcConfigTemperature);
        while (0U == (kCLOCK_PortB & ADC16_GetChannelStatusFlags(ADC_BASE, 0U))) {
            // Un pequeño truco visual para el delay de la conversión en simulación por polling
        }
        while (0U == (kADC16_ChannelConversionDoneFlag & ADC16_GetChannelStatusFlags(ADC_BASE, 0U))) {}
        temp_value = ADC16_GetChannelConversionValue(ADC_BASE, 0U);
        
        vTaskDelay(pdMS_TO_TICKS(500));
    }
}

static void vTaskButtonPolling(void *pvParameters)
{
    for (;;) {
        // Al usar resistencia de Pull-Up, el pin lee 0 cuando se presiona. Invertimos con '!'
        button_state = !GPIO_ReadPinInput(BUTTON_PORT, BUTTON_PIN);

        // EXPERIMENTO DE RESPONSIVIDAD: 
        // Cambia este delay a 200ms o 500ms para notar cómo se "pierden" los clicks del botón.
        vTaskDelay(pdMS_TO_TICKS(50));
    }
}

static void vTaskLedControl(void *pvParameters)
{
    while(1)
    {
        // Lógica de actuadores según el documento de la práctica
        
        // 1. Light value < 2048 -> ON Blue
        if(light_value < LIGHT_THRESHOLD){
            LED_BLUE_ON();
        } else {
            LED_BLUE_OFF();
        }

        // 2. Temperature value > 2048 -> ON Red (Ojo: corregida lógica inversa respecto a tu muestra)
        if (temp_value > TEMP_THRESHOLD){
            LED_RED_ON(); 
        } else {
            LED_RED_OFF();
        }

        // 3. Button pressed -> ON Green
        if(button_state){
            LED_GREEN_ON();
        } else {
            LED_GREEN_OFF();
        }

        // LA TRAMPA DE INEFICIENCIA: Despierta cada 200ms a procesar datos que cambian cada 500ms.
        vTaskDelay(pdMS_TO_TICKS(200));
    }
}

static void vTaskSerialMonitor(void *pvParameters)
{
    while(1)
    {
        PRINTF("Light (PTB1): %u | Temp (PTB2): %u | Button: %u\r\n",
                light_value,
                temp_value,
                button_state);

        vTaskDelay(pdMS_TO_TICKS(1500));
    }
}

#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include "FreeRTOS.h"
#include "task.h"
#include "queue.h"
#include "board.h"
#include "pin_mux.h"
#include "clock_config.h"
#include "fsl_debug_console.h"
#include "fsl_gpio.h"
#include "fsl_adc16.h"
#include "fsl_port.h" // <-- Añadida librería para registros de puerto

// Variables globales y tipos de datos
typedef enum
{
    SENSOR_LIGHT,
    SENSOR_TEMP,
    SENSOR_BUTTON
} sensor_type_t;

typedef struct
{
    sensor_type_t type;
    uint16_t value;
} sensor_msg_t;

// Definiciones de Hardware
#define BUTTON_PORT GPIOB
#define BUTTON_GPIO PORTB     // <-- Añadido para el Pull-Up
#define BUTTON_PIN 0U /* Assigned to PTB0 (J10 - pin 2 on the board)*/
#define ADC_BASE ADC0
#define ADC_CH_LIGHT 9U
#define ADC_CH_TEMPERATURE 12U

// Example thresholds
#define LIGHT_THRESHOLD 2500
#define TEMP_THRESHOLD 20     // Umbral ahora en grados Celsius directos (ej. 28°C)

QueueHandle_t sensorQueue;

// Prototipos de funciones
static void vTaskLightSensor(void *pvParameters);
static void vTaskTemperatureSensor(void *pvParameters);
static void vTaskButtonPolling(void *pvParameters);
static void vTaskLedControl(void *pvParameters);

int main(void) {
    /* Init board hardware. */
    BOARD_InitBootPins();
    BOARD_InitBootClocks();
    BOARD_InitDebugConsole();

    // ========================================================
    // CORRECCIÓN: CONFIGURACIÓN SEGURA DEL BOTÓN (PULL-UP)
    // ========================================================
    CLOCK_EnableClock(kCLOCK_PortB);
    PORT_SetPinMux(BUTTON_GPIO, BUTTON_PIN, kPORT_MuxAsGpio);
    BUTTON_GPIO->PCR[BUTTON_PIN] |= PORT_PCR_PE_MASK | PORT_PCR_PS_MASK; // Pull-Up Interno Activo

    gpio_pin_config_t button_gpio_config = {
        kGPIO_DigitalInput,
        0
    };
    GPIO_PinInit(BUTTON_PORT, BUTTON_PIN, &button_gpio_config);
    // ========================================================

    adc16_config_t adc16ConfigStruct;
    ADC16_GetDefaultConfig(&adc16ConfigStruct);
    adc16ConfigStruct.resolution = kADC16_ResolutionSE12Bit;
    adc16ConfigStruct.enableContinuousConversion = false;
    ADC16_Init(ADC_BASE, &adc16ConfigStruct);
    ADC16_EnableHardwareTrigger(ADC_BASE, false);
    ADC16_DoAutoCalibration(ADC_BASE);

    sensorQueue = xQueueCreate(10, sizeof(sensor_msg_t));

    if(sensorQueue == NULL)
    {
        PRINTF("Error creating queue\r\n");
        while(1);
    }

    PRINTF("FreeRTOS KL25z - Stage 3: ADC Math and Queue Mechanics\r\n");

    // Definición e inicio de tareas
    xTaskCreate(vTaskLightSensor, "Light", configMINIMAL_STACK_SIZE + 100, NULL, 2, NULL);
    xTaskCreate(vTaskTemperatureSensor, "Temp", configMINIMAL_STACK_SIZE + 100, NULL, 2, NULL);
    xTaskCreate(vTaskButtonPolling, "Button", configMINIMAL_STACK_SIZE + 100, NULL, 1, NULL);
    xTaskCreate(vTaskLedControl, "LEDs", configMINIMAL_STACK_SIZE + 100, NULL, 3, NULL);

    vTaskStartScheduler();
    while(1){}
}

static void vTaskLightSensor(void *pvParameters)
{
    sensor_msg_t msg;
    adc16_channel_config_t adcConfigLight;
    adcConfigLight.channelNumber = ADC_CH_LIGHT;
    adcConfigLight.enableInterruptOnConversionCompleted = false;
    adcConfigLight.enableDifferentialConversion = false;

    while(1)
    {
        ADC16_SetChannelConfig(ADC_BASE, 0U, &adcConfigLight);
        while (0U == (kADC16_ChannelConversionDoneFlag & ADC16_GetChannelStatusFlags(ADC_BASE, 0U))) {}

        msg.type = SENSOR_LIGHT;
        msg.value = ADC16_GetChannelConversionValue(ADC_BASE, 0U);

        xQueueSend(sensorQueue, &msg, pdMS_TO_TICKS(10));
        vTaskDelay(pdMS_TO_TICKS(500));
    }
}

static void vTaskTemperatureSensor(void *pvParameters){
    sensor_msg_t msg;
    adc16_channel_config_t adcConfigTemperature;
    adcConfigTemperature.channelNumber = ADC_CH_TEMPERATURE;
    adcConfigTemperature.enableInterruptOnConversionCompleted = false;
    adcConfigTemperature.enableDifferentialConversion = false;

    while(1){
        ADC16_SetChannelConfig(ADC_BASE, 0U, &adcConfigTemperature);
        while (0U == (kADC16_ChannelConversionDoneFlag & ADC16_GetChannelStatusFlags(ADC_BASE, 0U))) {}

        uint16_t result;
        // CORRECCIÓN: Se cambió 'ADC_Base' por 'ADC_BASE' (Mayúsculas fijadas)
        result = ADC16_GetChannelConversionValue(ADC_BASE, 0U);

        // Conversión matemática a grados Celsius (Para sensores tipo LM35)
        float voltage_mv;
        voltage_mv = (result * 3300.0f) / 4096.0f;
        float temperature_c;
        temperature_c = voltage_mv / 10.0f;

        msg.type = SENSOR_TEMP;
        msg.value = (uint16_t)temperature_c; // Enviamos el valor ya convertido en °C

        xQueueSend(sensorQueue, &msg, pdMS_TO_TICKS(10));
        vTaskDelay(pdMS_TO_TICKS(500));
    }
}

static void vTaskButtonPolling(void *pvParameters)
{
    sensor_msg_t msg;
    // CORRECCIÓN: Lógica inicializada en 0 por defecto
    uint32_t button_state = 0;
    uint32_t last_state = 0;

    for (;;) {
        // CORRECCIÓN: Inversión de lectura física con '!'
        button_state = !GPIO_ReadPinInput(BUTTON_PORT, BUTTON_PIN);

        if (button_state == 1 && last_state == 0) {
            // Flanco de subida lógico (Boton presionado físicamente)
        }
        last_state = button_state;

        msg.type = SENSOR_BUTTON;
        msg.value = button_state;
        xQueueSend(sensorQueue, &msg, pdMS_TO_TICKS(10));

        vTaskDelay(pdMS_TO_TICKS(50));
    }
}

static void vTaskLedControl(void *pvParameters)
{
    sensor_msg_t msg;
    uint16_t light_value = 0;
    uint16_t temp_value = 0;
    uint16_t button_value = 0;

    while(1)
    {
        if(xQueueReceive(sensorQueue, &msg, portMAX_DELAY) == pdPASS)
        {
            switch(msg.type)
            {
                case SENSOR_LIGHT:
                    light_value = msg.value;
                    break;
                case SENSOR_TEMP:
                    temp_value = msg.value;
                    break;
                case SENSOR_BUTTON:
                    button_value = msg.value;
                    break;
            }

            // Monitor de Consola Activo para verificar la conversión matemática
            PRINTF("Data -> Light ADC: %u | Temp: %u C | Button: %u\r\n",
                    light_value,
                    temp_value,
                    button_value);

            // Control LED Azul (Luz)
            if(light_value < LIGHT_THRESHOLD)
                LED_BLUE_ON();
            else
                LED_BLUE_OFF();

            // CORRECCIÓN: Lógica del LED Rojo invertida para coincidir con la KL25Z
            if(temp_value > TEMP_THRESHOLD)
                LED_RED_OFF();
            else
                LED_RED_ON();

            // CORRECCIÓN: LED Verde directo con el botón invertido (1 = Presionado = ON)
            if(button_value)
                LED_GREEN_ON();
            else
                LED_GREEN_OFF();
        }
    }
}

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
#include "fsl_port.h"

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

#define BUTTON_PORT GPIOB
#define BUTTON_GPIO PORTB
#define BUTTON_PIN 0U
#define ADC_BASE ADC0
#define ADC_CH_LIGHT 9U
#define ADC_CH_TEMPERATURE 12U

#define LIGHT_THRESHOLD 2048
#define TEMP_THRESHOLD 2048

QueueHandle_t sensorQueue;

static void vTaskLightSensor(void *pvParameters);
static void vTaskTemperatureSensor(void *pvParameters);
static void vTaskButtonPolling(void *pvParameters);
static void vTaskLedControl(void *pvParameters);

int main(void) {
    BOARD_InitBootPins();
    BOARD_InitBootClocks();
    BOARD_InitDebugConsole();

    CLOCK_EnableClock(kCLOCK_PortB);
    PORT_SetPinMux(BUTTON_GPIO, BUTTON_PIN, kPORT_MuxAsGpio);
    BUTTON_GPIO->PCR[BUTTON_PIN] |= PORT_PCR_PE_MASK | PORT_PCR_PS_MASK;

    gpio_pin_config_t button_gpio_config = {
        kGPIO_DigitalInput,
        0
    };
    GPIO_PinInit(BUTTON_PORT, BUTTON_PIN, &button_gpio_config);

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

    PRINTF("FreeRTOS KL25z - Stage 2: Queue mechanics active\r\n");

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

static void vTaskTemperatureSensor(void *pvParameters)
{
    sensor_msg_t msg;
    adc16_channel_config_t adcConfigTemperature;
    adcConfigTemperature.channelNumber = ADC_CH_TEMPERATURE;
    adcConfigTemperature.enableInterruptOnConversionCompleted = false;
    adcConfigTemperature.enableDifferentialConversion = false;

    while(1){
        ADC16_SetChannelConfig(ADC_BASE, 0U, &adcConfigTemperature);
        while (0U == (kADC16_ChannelConversionDoneFlag & ADC16_GetChannelStatusFlags(ADC_BASE, 0U))) {}

        msg.type = SENSOR_TEMP;
        msg.value = ADC16_GetChannelConversionValue(ADC_BASE, 0U);

        xQueueSend(sensorQueue, &msg, pdMS_TO_TICKS(10));
        vTaskDelay(pdMS_TO_TICKS(500));
    }
}

static void vTaskButtonPolling(void *pvParameters)
{
    sensor_msg_t msg;
    uint32_t button_state = 0;
    uint32_t last_state = 0;

    for (;;) {
        button_state = !GPIO_ReadPinInput(BUTTON_PORT, BUTTON_PIN);

        if (button_state == 1 && last_state == 0) {
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

            PRINTF("Light: %u | Temp: %u | Button: %u\r\n",
                    light_value,
                    temp_value,
                    button_value);

            if(light_value < LIGHT_THRESHOLD)
                LED_BLUE_ON();
            else
                LED_BLUE_OFF();

            if(temp_value > TEMP_THRESHOLD)
                LED_RED_OFF();
            else
                LED_RED_ON();

            if(button_value)
                LED_GREEN_ON();
            else
                LED_GREEN_OFF();
        }
    }
}

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

//variables globales
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

//definimos
#define BUTTON_PORT GPIOB
#define BUTTON_PIN 0U /* Assigned to PTB0 (J10 - pin 2 on the board)*/
#define ADC_BASE ADC0
#define ADC_CH_LIGHT 9U
#define ADC_CH_TEMPERATURE 12U

//example thresholds
#define LIGHT_THRESHOLD 1500
#define TEMP_THRESHOLD 28

QueueHandle_t sensorQueue;

//prototypes
static void vTaskLightSensor(void *pvParameters);
static void vTaskTemperatureSensor(void *pvParameters);
static void vTaskButtonPolling(void *pvParameters);
static void vTaskLedControl(void *pvParameters);

int main(void) {
    /* Init board hardware. */
    BOARD_InitBootPins();
    BOARD_InitBootClocks();
    BOARD_InitDebugConsole();

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

    PRINTF("FreeRTOS KL25z - Tasks with sensors without queues or interruptions\r\n");

    // Definición de tareas
    xTaskCreate(vTaskLightSensor, "Light", configMINIMAL_STACK_SIZE + 100,
    		NULL,
    		2,
    		NULL);
    // Inciamos las tareas
    xTaskCreate(vTaskTemperatureSensor,
    		"Temp",
			configMINIMAL_STACK_SIZE + 100,
			NULL,
			2,
			NULL);
    xTaskCreate(vTaskButtonPolling,
    		"Button",
			configMINIMAL_STACK_SIZE + 100,
			NULL,
			1,
			NULL);
    xTaskCreate(vTaskLedControl,
    		"LEDs",
			configMINIMAL_STACK_SIZE + 100,
			NULL,
			3,
			NULL);
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
		/* Trigger conversion */
		ADC16_SetChannelConfig(ADC_BASE, 0U, &adcConfigLight);
		/* Wait for conversion to end */
		while (0U == (kADC16_ChannelConversionDoneFlag & ADC16_GetChannelStatusFlags(ADC_BASE, 0U))) {}
		/* Read result */
		msg.type = SENSOR_LIGHT;
		/* Read result */
		msg.value = ADC16_GetChannelConversionValue(ADC_BASE, 0U);;
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
		result = ADC16_GetChannelConversionValue(ADC_Base, 0U);
		float voltage_mv; //voltage miliVolts
		voltage_mv = (result * 3300.0f)/4096.0f;
		float temperature_c;
		temperature_c = voltage_mv/10.0f;

		msg.type = SENSOR_TEMP;
		/* Read result */
		msg.value = (uint16_t)temperature_c;
		xQueueSend(sensorQueue, &msg, pdMS_TO_TICKS(10));
		vTaskDelay(pdMS_TO_TICKS(500));
	}

}

static void vTaskButtonPolling(void *pvParameters)
{
	sensor_msg_t msg;
	uint32_t button_state = 1;
	uint32_t last_state = 1; /* Physical or internal Pull-Up configuration assumed */
	for (;;) {
		button_state = GPIO_ReadPinInput(BUTTON_PORT, BUTTON_PIN);
		/* Falling edge detection */
		if (button_state == 0 && last_state == 1) {
			// PRINTF("Event: Button pressed.\r\n");
			last_state = button_state;
		}
		msg.type = SENSOR_BUTTON;
		msg.value = button_state;
		xQueueSend(sensorQueue, &msg, pdMS_TO_TICKS(10));

		/* 50ms blocking. Acts as a button debounce */
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
		if(xQueueReceive(sensorQueue, &msg, portMAX_DELAY) ==
		pdPASS)
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
			if(light_value < LIGHT_THRESHOLD)
				LED_BLUE_ON();
			else
				LED_BLUE_OFF();
			if(temp_value > TEMP_THRESHOLD)
				LED_RED_ON();
			else
				LED_RED_OFF();
			if(!button_value)
				LED_GREEN_ON();
			else
				LED_GREEN_OFF();
		}
	}
}


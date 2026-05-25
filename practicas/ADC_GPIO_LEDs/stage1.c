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

//variables globales
volatile uint16_t light_value = 0;
volatile uint16_t temp_value = 0;
volatile uint16_t button_state = 1;

//definimos
#define BUTTON_PORT GPIOB
#define BUTTON_PIN 0U /* Assigned to PTB0 (J10 - pin 2 on the board)*/
#define ADC_BASE ADC0
#define ADC_CH_LIGHT 9U
#define ADC_CH_TEMPERATURE 12U

//example thresholds
#define LIGHT_THRESHOLD 2048
#define TEMP_THRESHOLD 2048

//prototypes
static void vTaskLightSensor(void *pvParameters);
static void vTaskTemperatureSensor(void *pvParameters);
static void vTaskButtonPolling(void *pvParameters);
static void vTaskLedControl(void *pvParameters);
static void vTaskSerialMonitor(void *pvParameters);

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

    PRINTF("FreeRTOS KL25z - Tasks with sensors without queues or interruptions\r\n");

	// Tareas
    xTaskCreate(vTaskBoton, "Light", configMINIMAL_STACK_SIZE + 100,
    		NULL,
    		2,
    		NULL);
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
    xTaskCreate(vTaskSerialMonitor,
    "Serial",
    configMINIMAL_STACK_SIZE + 200,
    NULL,
    1,
    NULL);
    vTaskStartScheduler();
    while(1){}
}

static void vTaskLightSensor(void *pvParameters)
{
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
		light_value = ADC16_GetChannelConversionValue(ADC_BASE,
0U);
		vTaskDelay(pdMS_TO_TICKS(500));
	}
}

static void TaskTemperatureSensor(void *pvParameters){
	adc16_channel_config_t adcConfigTemperature;
	adcConfigTemperature.channelNumber = ADC_CH_TEMPERATURE;
	adcConfigTemperature.enableInterruptOnConversionCompleted =
false;
	adcConfigTemperature.enableDifferentialConversion = false;
	while(1){
		ADC16_SetChannelConfig(ADC_BASE, 0U, &adcConfigTemperature);
		while (0U == (kADC16_ChannelConversionDoneFlag & ADC16_GetChannelStatusFlags(ADC_BASE, 0U))) {}
		vTaskDelay(pdMS_TO_TICKS(500));
	}

}

static void vTaskButtonPolling(void *pvParameters)
{
	uint32_t last_state = 1; /* Physical or internal Pull-Up configuration assumed */
	for (;;) {
		button_state = GPIO_ReadPinInput(BUTTON_PORT, BUTTON_PIN);
		/* Falling edge detection */
		if (button_state == 0 && last_state == 1) {
			// PRINTF("Event: Button pressed.\r\n");
		}
		last_state = button_state;
		/* 50ms blocking. Acts as a button debounce */
		vTaskDelay(pdMS_TO_TICKS(50));
	}
}

static void vTaskLedControl(void *pvParameters)
{
	while(1)
	{
		if(light_value < LIGHT_THRESHOLD){
			LED_BLUE_ON();
		}
		else{
			LED_BLUE_OFF();
		}
		if (temp_value > TEMP_THRESHOLD){
    		LED_RED_ON();
    	}
    	else{
    		LED_RED_OFF();
    	}
    	if(!button_state){
    		LED_GREEN_ON();
    	}
    	else{
    		LED_GREEN_OFF();
    	}
    	vTaskDelay(pdMS_TO_TICKS(200));
	}
}

static void vTaskSerialMonitor(void *pvParameters)
{
	while(1)
	{
		PRINTF("Light: %u | Temp: %u | Button: %u\r\n",
				light_value,
				temp_value,
				button_state);
		vTaskDelay(pdMS_TO_TICKS(1500));
	}
}

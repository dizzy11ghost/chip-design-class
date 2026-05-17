#include "MKL25Z4.h"
#include <stdint.h>

#define TRIG_PIN 12u
#define ECHO_PIN 4u

#define RED_LED_PIN   18u
#define GREEN_LED_PIN 19u
#define BLUE_LED_PIN   1u

#define MOTOR_PINS    ((1<<5)|(1<<6)|(1<<7)|(1<<8))
#define STEPS_PER_REV 512

#define OBSTACLE_CM   25.0f

void  Init_LEDs(void);
void  UART0_Init(void);
void  UART0_SendChar(char c);
void  UART0_SendString(const char *s);
void  TPM0_Echo_Init(void);
float medir_distancia(void);
void  SendMeasurement(int angulo, float distancia);
void  delayMs(int n);
void  stepForward(void);
void  stepBackward(void);

//LEDs -------------------------------------------------------------
void Init_LEDs(void)
{
    SIM->SCGC5 |= SIM_SCGC5_PORTB_MASK | SIM_SCGC5_PORTD_MASK;

    PORTB->PCR[RED_LED_PIN]   = PORT_PCR_MUX(1);
    PORTB->PCR[GREEN_LED_PIN] = PORT_PCR_MUX(1);
    PORTD->PCR[BLUE_LED_PIN]  = PORT_PCR_MUX(1);

    PTB->PDDR |= (1u << RED_LED_PIN) | (1u << GREEN_LED_PIN);
    PTD->PDDR |= (1u << BLUE_LED_PIN);

    // LEDs apagados
    PTB->PSOR = (1u << RED_LED_PIN) | (1u << GREEN_LED_PIN);
    PTD->PSOR = (1u << BLUE_LED_PIN);
}

//UART0 con 9600 Baudios -----------------------------------------
void UART0_Init(void)
{
    SIM->SCGC4 |= SIM_SCGC4_UART0_MASK;
    SIM->SCGC5 |= SIM_SCGC5_PORTA_MASK;

    // PTA2 = UART0_TX
    PORTA->PCR[2] = PORT_PCR_MUX(2);

    // Fuente de clock UART0
    SIM->SOPT2 |= SIM_SOPT2_UART0SRC(1);

    // Deshabilitar UART antes de configurar
    UART0->C2 = 0x00;

    // 9600 baud para clock ~21 MHz
    UART0->BDH = 0x00;
    UART0->BDL = 0x88;

    UART0->C1 = 0x00;
    UART0->S2 = 0x00;
    UART0->C3 = 0x00;

    // Oversampling = 16
    UART0->C4 = 0x0F;

    // Habilitar TX
    UART0->C2 = UART0_C2_TE_MASK;
}

void UART0_SendChar(char c)
{
    while (!(UART0->S1 & UART0_S1_TDRE_MASK));

    UART0->D = (uint8_t)c;
}

void UART0_SendString(const char *s)
{
    while (*s)
    {
        UART0_SendChar(*s++);
    }
}

//sensor ultrasónico ------------------------------------------------

void TPM0_Echo_Init(void)
{
    SIM->SCGC6 |= SIM_SCGC6_TPM0_MASK; //usamos TPM0
    SIM->SCGC5 |= SIM_SCGC5_PORTA_MASK | SIM_SCGC5_PORTD_MASK;

    // Clock TPM
    SIM->SOPT2 |= SIM_SOPT2_TPMSRC(1);

    // Trigger
    PORTA->PCR[TRIG_PIN] = PORT_PCR_MUX(1);
    PTA->PDDR |= (1u << TRIG_PIN);
    PTA->PCOR  = (1u << TRIG_PIN);

    // Echo
    PORTD->PCR[ECHO_PIN] = PORT_PCR_MUX(1);
    PTD->PDDR &= ~(1u << ECHO_PIN);

    TPM0->SC  = 0;
    TPM0->CNT = 0;
    TPM0->MOD = 0xFFFF;

    // Prescaler /32
    TPM0->SC = TPM_SC_PS(5) | TPM_SC_CMOD(1);
}

// medimos distancia del sensor
float medir_distancia(void)
{
    uint32_t ticks;
    uint32_t timeout;

    // Trigger de 10us aprox
    PTA->PSOR = (1u << TRIG_PIN);

    TPM0->CNT = 0;

    while (TPM0->CNT < 15u);

    PTA->PCOR = (1u << TRIG_PIN);

    // Esperar flanco subida
    timeout = 100000u;

    while (!(PTD->PDIR & (1u << ECHO_PIN)) && --timeout);

    if (timeout == 0u)
        return -1.0f;

    TPM0->CNT = 0;

    // Esperar flanco bajada
    timeout = 1000000u;

    while ((PTD->PDIR & (1u << ECHO_PIN)) && --timeout);

    if (timeout == 0u)
        return -1.0f;

    ticks = TPM0->CNT;

    // Conversión aproximada a cm
    return (float)ticks * 0.01145f;
}

//enviamos datos: distancia, ángulo
void SendMeasurement(int angulo, float distancia)
{
    char buf[32];
    uint8_t idx = 0;

    int32_t entero;
    int32_t decimals;

    // Ángulo
    if (angulo >= 100)
        buf[idx++] = '0' + angulo / 100;

    if (angulo >= 10)
        buf[idx++] = '0' + ((angulo / 10) % 10);

    buf[idx++] = '0' + (angulo % 10);

    buf[idx++] = ',';

    // Timeout
    if (distancia < 0.0f)
    {
        buf[idx++] = '-';
        buf[idx++] = '1';
        buf[idx++] = '\n';
        buf[idx] = '\0';

        UART0_SendString(buf);
        return;
    }

    entero = (int32_t)distancia;

    decimals = (int32_t)((distancia - (float)entero) * 100.0f);

    if (entero >= 100)
        buf[idx++] = '0' + entero / 100;

    if (entero >= 10)
        buf[idx++] = '0' + ((entero / 10) % 10);

    buf[idx++] = '0' + (entero % 10);

    buf[idx++] = '.';

    buf[idx++] = '0' + (decimals / 10);
    buf[idx++] = '0' + (decimals % 10);

    buf[idx++] = '\n';

    buf[idx] = '\0';

    UART0_SendString(buf);
}

void delayMs(int n)
{
    int i;

    SysTick->LOAD = 48000 - 1;  // 1 ms a 48 MHz
    SysTick->VAL  = 0;
    SysTick->CTRL = 0x5;

    for(i = 0; i < n; i++)
    {
        while((SysTick->CTRL & 0x10000) == 0);
    }

    SysTick->CTRL = 0;
}

//stepper forward (motor) --------------------------------------------
void stepForward(void)
{
    PTC->PCOR = MOTOR_PINS;
    PTC->PSOR = (1<<5);
    delayMs(1);

    PTC->PCOR = MOTOR_PINS;
    PTC->PSOR = (1<<7);
    delayMs(1);

    PTC->PCOR = MOTOR_PINS;
    PTC->PSOR = (1<<6);
    delayMs(1);

    PTC->PCOR = MOTOR_PINS;
    PTC->PSOR = (1<<8);
    delayMs(1);
}

//stepper backwards
void stepBackward(void)
{
    PTC->PCOR = MOTOR_PINS;
    PTC->PSOR = (1<<8);
    delayMs(1);

    PTC->PCOR = MOTOR_PINS;
    PTC->PSOR = (1<<6);
    delayMs(1);

    PTC->PCOR = MOTOR_PINS;
    PTC->PSOR = (1<<7);
    delayMs(1);

    PTC->PCOR = MOTOR_PINS;
    PTC->PSOR = (1<<5);
    delayMs(1);
}

// main ---------------------------------------------------------------
int main(void)
{
    float distancia;
    int angulo;
    int i;

    Init_LEDs();

    UART0_Init();

    TPM0_Echo_Init();

    // Puerto C para motor
    SIM->SCGC5 |= SIM_SCGC5_PORTC_MASK;

    PORTC->PCR[5] = PORT_PCR_MUX(1);
    PORTC->PCR[6] = PORT_PCR_MUX(1);
    PORTC->PCR[7] = PORT_PCR_MUX(1);
    PORTC->PCR[8] = PORT_PCR_MUX(1);

    PTC->PDDR |= MOTOR_PINS;

    PTC->PCOR = MOTOR_PINS;

    while (1)
    {
        // Barrido adelante
        for (i = 0; i < STEPS_PER_REV; i++)
        {
            stepForward();

            distancia = medir_distancia();

            angulo = (i * 360) / STEPS_PER_REV;

            //LED azul si detecta obstáculo para debuggear visualmente
            if (distancia > 0.0f && distancia < OBSTACLE_CM)
                PTD->PCOR = (1u << BLUE_LED_PIN);
            else
                PTD->PSOR = (1u << BLUE_LED_PIN);

            SendMeasurement(angulo, distancia);
        }

        // Barrido atrás
        for (i = 0; i < STEPS_PER_REV; i++)
        {
            stepBackward();

            distancia = medir_distancia();

            angulo = 360 - ((i * 360) / STEPS_PER_REV);

            if (distancia > 0.0f && distancia < OBSTACLE_CM)
                PTD->PCOR = (1u << BLUE_LED_PIN);
            else
                PTD->PSOR = (1u << BLUE_LED_PIN);

            SendMeasurement(angulo, distancia);
        }

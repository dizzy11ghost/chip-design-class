#include "MKL25Z4.h"
#include <stdio.h>

#define PWM_MAX_VAL       4800
#define PWM_MAX_CORR      4800
#define PWM_BASE          4560
#define PWM_MIN           4320
#define PULSOS_POR_CM     12.78f
#define KP                1

volatile uint32_t pulsosIzq = 0;
volatile uint32_t pulsosDer = 0;

uint8_t estadoAntIzq = 0;
uint8_t estadoAntDer = 0;

void delay_ms(uint32_t ms);
void Motor_Init(void);
void PWM_init(void);
void PWM_Set(uint16_t pwmDer, uint16_t pwmIzq);
void Encoder_Init(void);
void Motores_Adelante(void);
void Motores_Stop(void);
void Actualizar_Encoders(void);
void Mover_Distancia(float cm, uint8_t reversa);
void UART0_init(uint32_t baud);
void UART0_SendChar(char c);
void UART0_SendStr(const char *str);
uint8_t UART0_RecvChar(char *c);
void UART0_RecvCmd(char *buf, uint8_t len);
void Procesar_Comando(char *cmd);

int main(void)
{
	Motor_Init();
	PWM_init();
	Encoder_Init();
	UART0_init(9600);

	char cmd[3];

    while(1) {
    	UART0_RecvCmd(cmd, 3);
    	Procesar_Comando(cmd);
    }

    return 0;
}

void delay_ms(uint32_t ms) {
    for (uint32_t i = 0; i < ms * 2400UL; i++)
        __asm volatile ("nop");
}

void Motor_Init(void)
{
    SIM->SCGC5 |= SIM_SCGC5_PORTC_MASK;

    PORTC->PCR[0] = PORT_PCR_MUX(1);
    PORTC->PCR[1] = PORT_PCR_MUX(1);
    PORTC->PCR[2] = PORT_PCR_MUX(1);
    PORTC->PCR[3] = PORT_PCR_MUX(1);

    GPIOC->PDDR |= (1<<0)|(1<<1)|(1<<2)|(1<<3);
}

void PWM_init(void)
{
    SIM->SCGC5 |= SIM_SCGC5_PORTB_MASK;

    PORTB->PCR[0] = PORT_PCR_MUX(3);   // Motor derecho
    PORTB->PCR[1] = PORT_PCR_MUX(3);   // Motor izquierdo

    SIM->SCGC6 |= SIM_SCGC6_TPM1_MASK;
    SIM->SOPT2  |= SIM_SOPT2_TPMSRC(1);
    SIM->SOPT4  &= ~SIM_SOPT4_TPM1CH0SRC_MASK;

    TPM1->SC = 0;
    TPM1->MOD = PWM_MAX_VAL;

    TPM1->CONTROLS[0].CnSC = TPM_CnSC_MSB_MASK | TPM_CnSC_ELSB_MASK;
    TPM1->CONTROLS[1].CnSC = TPM_CnSC_MSB_MASK | TPM_CnSC_ELSB_MASK;

    TPM1->CONTROLS[0].CnV = 0;
    TPM1->CONTROLS[1].CnV = 0;

    TPM1->SC = TPM_SC_CMOD(1);
}

void PWM_Set(uint16_t pwmDer, uint16_t pwmIzq)
{
    TPM1->CONTROLS[0].CnV = pwmDer;
    TPM1->CONTROLS[1].CnV = pwmIzq;
}

void Encoder_Init(void)
{
    SIM->SCGC5 |= SIM_SCGC5_PORTE_MASK;

    PORTE->PCR[20] = PORT_PCR_MUX(1) | PORT_PCR_PE_MASK | PORT_PCR_PS_MASK;
    PORTE->PCR[21] = PORT_PCR_MUX(1) | PORT_PCR_PE_MASK | PORT_PCR_PS_MASK;

    GPIOE->PDDR &= ~((1<<20)|(1<<21));

    estadoAntIzq = (GPIOE->PDIR >> 20) & 1;
    estadoAntDer = (GPIOE->PDIR >> 21) & 1;
}

void Motores_Adelante(void)
{
    // Izquierdo adelante
    GPIOC->PCOR = (1<<0);
    GPIOC->PSOR = (1<<1);

    // Derecho adelante
    GPIOC->PCOR = (1<<2);
    GPIOC->PSOR = (1<<3);
}

void Motores_Atras(void)
{
    // Izquierdo reversa
    GPIOC->PSOR = (1<<0);
    GPIOC->PCOR = (1<<1);

    // Derecho reversa
    GPIOC->PSOR = (1<<2);
    GPIOC->PCOR = (1<<3);
}

void Motores_Stop(void)
{
    PWM_Set(0, 0);
    GPIOC->PCOR = (1<<0)|(1<<1)|(1<<2)|(1<<3);
}

void Actualizar_Encoders(void)
{
    uint8_t estadoIzq = (GPIOE->PDIR >> 20) & 1;
    uint8_t estadoDer = (GPIOE->PDIR >> 21) & 1;

    if(estadoIzq != estadoAntIzq) { pulsosIzq++; estadoAntIzq = estadoIzq; }
    if(estadoDer != estadoAntDer) { pulsosDer++; estadoAntDer = estadoDer; }
}

void Mover_Distancia(float cm, uint8_t reversa)
{
    uint32_t objetivo = (uint32_t)(cm * PULSOS_POR_CM);

    pulsosIzq = 0;
    pulsosDer = 0;

    estadoAntIzq = (GPIOE->PDIR >> 20) & 1;
    estadoAntDer = (GPIOE->PDIR >> 21) & 1;

    if(reversa)
        Motores_Atras();
    else
        Motores_Adelante();

    PWM_Set(PWM_BASE, PWM_BASE);

    while(1)
    {
        Actualizar_Encoders();

        uint32_t promedio = (pulsosIzq + pulsosDer) / 2;

        int32_t error = (int32_t)pulsosIzq - (int32_t)pulsosDer;

        int32_t pwmIzq, pwmDer;

        if(error > 2 || error < -2)
        {
            pwmIzq = PWM_BASE - error * KP;
            pwmDer = PWM_BASE + error * KP;
        }
        else
        {
            pwmIzq = PWM_BASE;
            pwmDer = PWM_BASE;
        }

        if(pwmIzq > PWM_MAX_CORR) pwmIzq = PWM_MAX_CORR;
        if(pwmDer > PWM_MAX_CORR) pwmDer = PWM_MAX_CORR;
        if(pwmIzq < PWM_MIN)      pwmIzq = PWM_MIN;
        if(pwmDer < PWM_MIN)      pwmDer = PWM_MIN;

        PWM_Set((uint16_t)pwmDer, (uint16_t)pwmIzq);

        if(promedio >= objetivo)
        {
            Motores_Stop();
            break;
        }
    }
}

void UART0_init(uint32_t baud) {
    MCG->C4 |= MCG_C4_DMX32_MASK;
    MCG->C4  = (MCG->C4 & ~MCG_C4_DRST_DRS_MASK) | MCG_C4_DRST_DRS(1);
    SIM->CLKDIV1 = SIM_CLKDIV1_OUTDIV1(0) | SIM_CLKDIV1_OUTDIV4(1);
    SIM->SOPT2  |= SIM_SOPT2_UART0SRC(1);
    SIM->SCGC4  |= SIM_SCGC4_UART0_MASK;
    SIM->SCGC5  |= SIM_SCGC5_PORTA_MASK;
    PORTA->PCR[1] = PORT_PCR_MUX(2);
    PORTA->PCR[2] = PORT_PCR_MUX(2);
    UART0->C2 = 0;
    uint16_t sbr = 48000000u / (16u * baud);
    UART0->BDH = (uint8_t)((sbr >> 8) & 0x1F);
    UART0->BDL = (uint8_t)(sbr & 0xFF);
    UART0->C4  = 0x0F;
    UART0->C1  = 0;
    UART0->C2  = UART0_C2_TE_MASK | UART0_C2_RE_MASK;
}

void UART0_SendChar(char c)
{
    while(!(UART0->S1 & UART0_S1_TDRE_MASK));
    UART0->D = c;
}

void UART0_SendStr(const char *str)
{
    while(*str)
        UART0_SendChar(*str++);
}

uint8_t UART0_RecvChar(char *c)
{
    if(UART0->S1 & UART0_S1_RDRF_MASK)
    {
        *c = UART0->D;
        return 1;
    }
    return 0;
}

void UART0_RecvCmd(char *buf, uint8_t len)
{
    for(uint8_t i = 0; i < len; i++)
    {
        while(!(UART0->S1 & UART0_S1_RDRF_MASK));
        buf[i] = UART0->D;
    }
}

void Procesar_Comando(char *cmd)
{
    // KUB → avanzar 70 cm
    if(cmd[0]=='K' && cmd[1]=='U' && cmd[2]=='B')
    {
        Mover_Distancia(70, 0);
        UART0_SendStr("RL");
    }
    // KBU → retroceder 70 cm
    else if(cmd[0]=='K' && cmd[1]=='B' && cmd[2]=='U')
    {
        Mover_Distancia(70, 1);
        UART0_SendStr("RR");
    }
}

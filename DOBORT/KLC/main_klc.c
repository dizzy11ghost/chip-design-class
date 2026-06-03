#include "MKL25Z4.h"
#include <stdlib.h> // Para la función atoi

void LED_init(void);
void LED_set(int rojo, int verde, int azul);
void UART0_init(uint32_t baud);
char UART0_receive_char(void);
char UART0_check_rx(void);
void delay_ms(uint32_t ms);

void MOTORES_init(void);
void PWM_init(void);
void motores_avanzar(uint16_t velocidad_motor_1, uint16_t velocidad_motor_2);
void motores_reversa(uint16_t velocidad_motor_1, uint16_t velocidad_motor_2);
void motores_detener(void);

#define LOOPS_PER_MS  2400UL

// Definición de estados del Carrito
typedef enum {
    ESPERANDO_COMANDO,
    AVANZANDO,
    REVERSA
} EstadoCarrito;

void delay_ms(uint32_t ms) {
    for (uint32_t i = 0; i < ms * LOOPS_PER_MS; i++) {
        __asm volatile ("nop");
    }
}

void LED_init(void) {
    SIM->SCGC5 |= SIM_SCGC5_PORTB_MASK | SIM_SCGC5_PORTD_MASK;
    PORTB->PCR[18] = PORT_PCR_MUX(1); // LED Rojo
    PORTB->PCR[19] = PORT_PCR_MUX(1); // LED Verde
    PORTD->PCR[1]  = PORT_PCR_MUX(1); // LED Azul
    PTB->PDDR |= (1<<18) | (1<<19);
    PTD->PDDR |= (1<<1);
    PTB->PSOR  = (1<<18) | (1<<19);   // Apagados
    PTD->PSOR  = (1<<1);
}

void LED_set(int rojo, int verde, int azul) {
    if (rojo)  PTB->PCOR = (1<<18); else PTB->PSOR = (1<<18);
    if (verde) PTB->PCOR = (1<<19); else PTB->PSOR = (1<<19);
    if (azul)  PTD->PCOR = (1<<1);  else PTD->PSOR = (1<<1);
}

// Se mantiene tu configuración original de UART0
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
    uint16_t sbr = 48000000 / (16 * baud);
    UART0->BDH = (sbr >> 8) & 0x1F;
    UART0->BDL =  sbr & 0xFF;
    UART0->C4  = 0x0F;
    UART0->C1  = 0;
    UART0->C2  = UART0_C2_TE_MASK | UART0_C2_RE_MASK;
}

char UART0_receive_char(void) {
    while (!(UART0->S1 & UART0_S1_RDRF_MASK));
    return UART0->D;
}

// Verifica si hay datos listos en la UART0 sin bloquear el código
char UART0_check_rx(void) {
    if (UART0->S1 & UART0_S1_RDRF_MASK)
        return UART0->D;
    return 0;
}

void MOTORES_init(void) {
    SIM->SCGC5 |= SIM_SCGC5_PORTC_MASK;
    PORTC->PCR[0] = PORT_PCR_MUX(1); // IN1 -> PTC0
    PORTC->PCR[1] = PORT_PCR_MUX(1); // IN2 -> PTC1
    PORTC->PCR[2] = PORT_PCR_MUX(1); // IN3 -> PTC2
    PORTC->PCR[3] = PORT_PCR_MUX(1); // IN4 -> PTC3
    PTC->PDDR |= (1<<0) | (1<<1) | (1<<2) | (1<<3);
    PTC->PCOR = (1<<0) | (1<<1) | (1<<2) | (1<<3);
}

void PWM_init(void) {
    SIM->SCGC5 |= SIM_SCGC5_PORTB_MASK;
    PORTB->PCR[0] = PORT_PCR_MUX(3); // PTB0 -> TPM1_CH0 (ENA)
    PORTB->PCR[1] = PORT_PCR_MUX(3); // PTB1 -> TPM1_CH1 (ENB)

    SIM->SCGC6 |= SIM_SCGC6_TPM1_MASK;
    SIM->SOPT2 |= SIM_SOPT2_TPMSRC(1);

    TPM1->SC = 0;
    TPM1->CONTROLS[0].CnSC = TPM_CnSC_MSB_MASK | TPM_CnSC_ELSB_MASK;
    TPM1->CONTROLS[1].CnSC = TPM_CnSC_MSB_MASK | TPM_CnSC_ELSB_MASK;

    TPM1->MOD = 4800;
    TPM1->CONTROLS[0].CnV = 0;
    TPM1->CONTROLS[1].CnV = 0;

    TPM1->SC = TPM_SC_CMOD(1) | TPM_SC_PS(0);
}

void motores_avanzar(uint16_t velocidad_motor_1, uint16_t velocidad_motor_2) {
    PTC->PSOR = (1<<0); // IN1 = 1
    PTC->PCOR = (1<<1); // IN2 = 0
    PTC->PSOR = (1<<2); // IN3 = 1
    PTC->PCOR = (1<<3); // IN4 = 0
    TPM1->CONTROLS[0].CnV = velocidad_motor_1;
    TPM1->CONTROLS[1].CnV = velocidad_motor_2;
}

void motores_reversa(uint16_t velocidad_motor_1, uint16_t velocidad_motor_2) {
    PTC->PCOR = (1<<0); // IN1 = 0
    PTC->PSOR = (1<<1); // IN2 = 1
    PTC->PCOR = (1<<2); // IN3 = 0
    PTC->PSOR = (1<<3); // IN4 = 1
    TPM1->CONTROLS[0].CnV = velocidad_motor_1;
    TPM1->CONTROLS[1].CnV = velocidad_motor_2;
}

uint16_t porcentaje_a_pwm(uint8_t porcentaje) {
    if (porcentaje > 100) porcentaje = 100;
    return (TPM1->MOD * porcentaje) / 100;
}

void motores_detener(void) {
    PTC->PCOR = (1<<0) | (1<<1) | (1<<2) | (1<<3);
    TPM1->CONTROLS[0].CnV = 0;
    TPM1->CONTROLS[1].CnV = 0;
}

int main(void) {
    char buffer_rx[4] = {0};
    int indice_rx = 0;

    EstadoCarrito estadoActual = ESPERANDO_COMANDO;

    UART0_init(9600);
    LED_init();
    MOTORES_init();
    PWM_init();

    uint16_t velocidad_motor_1 = porcentaje_a_pwm(80);
    uint16_t velocidad_motor_2 = porcentaje_a_pwm(70);

    while (1) {
        char c = UART0_check_rx();

        if (c != 0) {
            buffer_rx[indice_rx] = c;
            indice_rx++;

            if (indice_rx == 3) {
                buffer_rx[3] = '\0';

                // KUB → Avanzar
                if (buffer_rx[0] == 'K' && buffer_rx[1] == 'U' && buffer_rx[2] == 'B') {
                    estadoActual = AVANZANDO;
                    motores_avanzar(velocidad_motor_1, velocidad_motor_2);
                }
                // KBU → Reversa
                else if (buffer_rx[0] == 'K' && buffer_rx[1] == 'B' && buffer_rx[2] == 'U') {
                    estadoActual = REVERSA;
                    motores_reversa(velocidad_motor_1, velocidad_motor_2);
                }
                // KST → Detener  ← NUEVO
                else if (buffer_rx[0] == 'K' && buffer_rx[1] == 'S' && buffer_rx[2] == 'T') {
                    motores_detener();
                    estadoActual = ESPERANDO_COMANDO;
                }

                indice_rx = 0;
            }
        }

        // LEDs según estado
        if (estadoActual == ESPERANDO_COMANDO) {
            LED_set(1, 0, 0); // Rojo
        } else if (estadoActual == AVANZANDO) {
            LED_set(0, 1, 0); // Verde
        } else if (estadoActual == REVERSA) {
            LED_set(0, 0, 1); // Azul
        }
    }
}

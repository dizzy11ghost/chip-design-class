#include "MKL25Z4.h"

void LED_init(void);
void LED_set(int rojo, int verde, int azul);
void UART1_init(uint32_t baud);
void UART1_send_char(char c);
char UART1_receive_char(void);
void UART0_init(uint32_t baud);
void UART0_send_char(char c);
void UART0_send_string(char *str);
char UART0_check_rx(void);
char UART0_receive_char(void);
void PB_init(void);
void delay_ms(uint32_t ms);
void routine_KL(void);   // Rutina 1
void routine_KR(void);   // Rutina 2

#define LOOPS_PER_MS  2400UL

void delay_ms(uint32_t ms) {
    for (uint32_t i = 0; i < ms * LOOPS_PER_MS; i++) {
        __asm volatile ("nop");
    }
}

void LED_init(void) {
    SIM->SCGC5 |= SIM_SCGC5_PORTB_MASK;
    PORTB->PCR[18] = PORT_PCR_MUX(1);
    PORTB->PCR[19] = PORT_PCR_MUX(1);
    PTB->PDDR |= (1<<18) | (1<<19);
    PTB->PSOR  = (1<<18) | (1<<19);

    SIM->SCGC5 |= SIM_SCGC5_PORTD_MASK;
    PORTD->PCR[1] = PORT_PCR_MUX(1);
    PTD->PDDR |= (1<<1);
    PTD->PSOR  = (1<<1);
}

void LED_set(int rojo, int verde, int azul) {
    if (rojo)  PTB->PCOR = (1<<18); else PTB->PSOR = (1<<18);
    if (verde) PTB->PCOR = (1<<19); else PTB->PSOR = (1<<19);
    if (azul)  PTD->PCOR = (1<<1);  else PTD->PSOR = (1<<1);
}


void PB_init(void) {
    SIM->SCGC5 |= SIM_SCGC5_PORTD_MASK;
    PORTD->PCR[2] = PORT_PCR_MUX(1) | PORT_PCR_PE_MASK | PORT_PCR_PS_MASK;
    PTD->PDDR &= ~(1<<2);
    PORTD->PCR[3] = PORT_PCR_MUX(1) | PORT_PCR_PE_MASK | PORT_PCR_PS_MASK;
    PTD->PDDR &= ~(1<<3);
}


void UART1_init(uint32_t baud) {
    SIM->SCGC4 |= SIM_SCGC4_UART1_MASK;
    SIM->SCGC5 |= SIM_SCGC5_PORTE_MASK;
    PORTE->PCR[0] = PORT_PCR_MUX(3);   /* TX */
    PORTE->PCR[1] = PORT_PCR_MUX(3);   /* RX */
    UART1->C2 = 0;
    uint16_t sbr = 24000000 / (16 * baud);
    UART1->BDH = (sbr >> 8) & 0x1F;
    UART1->BDL =  sbr & 0xFF;
    UART1->C1  = 0;
    UART1->C2  = UART_C2_TE_MASK | UART_C2_RE_MASK;
}

void UART1_send_char(char c) {
    while (!(UART1->S1 & UART_S1_TDRE_MASK));
    UART1->D = c;
}

char UART1_receive_char(void) {
    while (!(UART1->S1 & UART_S1_RDRF_MASK));
    return UART1->D;
}

void UART0_init(uint32_t baud) {
    MCG->C4 |= MCG_C4_DMX32_MASK;
    MCG->C4  = (MCG->C4 & ~MCG_C4_DRST_DRS_MASK) | MCG_C4_DRST_DRS(1);
    SIM->CLKDIV1 = SIM_CLKDIV1_OUTDIV1(0) | SIM_CLKDIV1_OUTDIV4(1);
    SIM->SOPT2  |= SIM_SOPT2_UART0SRC(1);
    SIM->SCGC4  |= SIM_SCGC4_UART0_MASK;
    SIM->SCGC5  |= SIM_SCGC5_PORTA_MASK;
    PORTA->PCR[1] = PORT_PCR_MUX(2);   /* RX */
    PORTA->PCR[2] = PORT_PCR_MUX(2);   /* TX */
    UART0->C2 = 0;
    uint16_t sbr = 48000000 / (16 * baud);
    UART0->BDH = (sbr >> 8) & 0x1F;
    UART0->BDL =  sbr & 0xFF;
    UART0->C4  = 0x0F;
    UART0->C1  = 0;
    UART0->C2  = UART0_C2_TE_MASK | UART0_C2_RE_MASK;
}

void UART0_send_char(char c) {
    while (!(UART0->S1 & UART0_S1_TDRE_MASK));
    UART0->D = c;
}

void UART0_send_string(char *str) {
    while (*str) UART0_send_char(*str++);
}

char UART0_check_rx(void) {
    if (UART0->S1 & UART0_S1_RDRF_MASK)
        return UART0->D;
    return 0;
}

char UART0_receive_char(void) {
    while (!(UART0->S1 & UART0_S1_RDRF_MASK));
    return UART0->D;
}

void routine_KL(void) {
    char b1, b2;
    LED_set(1,0,0);
    do {
        b1 = UART1_receive_char();
        b2 = UART1_receive_char();
    } while (!(b1 == 'K' && b2 == '1'));
    LED_set(0,1,0);
    delay_ms(500);
    LED_set(0,0,1);
    UART0_send_char('R');
    UART0_send_char('L');
    do {
        b1 = UART0_receive_char();
        b2 = UART0_receive_char();
    } while (!(b1 == 'K' && b2 == '2'));
    LED_set(1,0,0);
    delay_ms(500);
    UART1_send_char('M');
    UART1_send_char('L');
    LED_set(1,1,1);
}

void routine_KR(void) {
	LED_set(1,0,0);
	char b1, b2;
    do {
        b1 = UART1_receive_char();
        b2 = UART1_receive_char();
    } while (!(b1 == 'K' && b2 == 'R'));
    LED_set(0,0,1);
    delay_ms(500);
    UART0_send_char('R');
    UART0_send_char('E');
    LED_set(0,1,0);
    do {
        b1 = UART0_receive_char();
        b2 = UART0_receive_char();
    } while (!(b1 == 'K' && b2 == 'B'));
    delay_ms(500);
    UART1_send_char('M');
    UART1_send_char('R');
    LED_set(1,1,1);
}

int main(void) {
    UART0_init(9600);
    UART1_init(9600);
    LED_init();
    PB_init();
    while (1) {
        if (UART1->S1 & UART_S1_RDRF_MASK) {
            char dest = UART1->D;
            char dato = UART1_receive_char();
            if (dest == 'K') {
                switch (dato) {
                    case '1': LED_set(1,0,0); break;
                    case '2': LED_set(0,1,0); break;
                    case '3': LED_set(0,0,1); break;
                    case '4': LED_set(1,1,0); break;
                    case '5': LED_set(1,0,1); break;
                    case '6': LED_set(0,1,1); break;
                    case '7': LED_set(1,1,1); break;
                    case '0': LED_set(0,0,0); break;
                    default: break;
                }
            } else if (dest == 'R') {
                UART0_send_char(dest);
                UART0_send_char(dato);
            }
        }
        char rx = UART0_check_rx();
        if (rx != 0) {
            while (!(UART0->S1 & UART0_S1_RDRF_MASK));
            char dato = UART0->D;

            if (rx == 'S' && dato == 'B') {
                LED_set(0, 0, 1);
            } else if (rx == 'M') {
                UART1_send_char(rx);
                UART1_send_char(dato);
            }
        }
        if (!(PTD->PDIR & (1<<2))) {
            delay_ms(20);
            if (!(PTD->PDIR & (1<<2))) {
                routine_KL();
            }
        }
        if (!(PTD->PDIR & (1<<3))) {
            delay_ms(20);
            if (!(PTD->PDIR & (1<<3))) {
                routine_KR();
            }
        }
    }
}

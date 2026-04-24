#include <MKL25Z4.H>

void delayMs(int n);

int main(void) {
    SIM->SCGC6 |= 0x01000000;
    SIM->SOPT2 |= 0x01000000;
    TPM0->SC = 0;
    TPM0->SC = 0x02;
    TPM0->MOD = 0x2000;
    TPM0->SC |= 0x80;
    TPM0->SC |= 0x08;
    __disable_irq();

    SIM->SCGC5 |= 0x400;
    PORTB->PCR[18] = 0x100;     // LEd rojo
    PORTB->PCR[19] = 0x100;     // Led verde
    PTB->PDDR |= (1 << 18) | (1 << 19);
    PTB->PDOR |= (1 << 18) | (1 << 19);

    // Boton en el PTA1
    SIM->SCGC5 |= 0x200;
    PORTA->PCR[1] = 0x103;
    PTA->PDDR &= ~(1 << 1);

    // Interrupción
    PORTA->PCR[1] &= ~0xF0000;
    PORTA->PCR[1] |= 0xA0000;
    NVIC->ISER[0] |= 0x40000000;
    __enable_irq();

    while(1)
    {
        PTB->PTOR = (1 << 18);  // Led rojo parpadeando
        delayMs(500);
    }
}

void PORTA_IRQHandler(void) {
    int i;
    PTB->PDOR |= (1 << 18); // Apagar led rojo
    PTB->PTOR = (1 << 19);  // Led verde on
    delayMs(1000);

    PTB->PDOR |= (1 << 19); // Apagar led verde
    PORTA->ISFR = (1 << 1);
}

void delayMs(int n) {
    for(int i = 0; i < n; i++) {
        while((TPM0->SC & 0x80) == 0) { } /* Esperar al TOF */
        TPM0->SC |= 0x80;                 /* Limpiar TOF */
    }
}

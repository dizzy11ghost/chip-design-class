//Program (2): Multiple requests from single port
/* Toggles red LED while waiting for INT from SWs */
#include <MKL25Z4.h>

#define RS 0x04 /* PTA2 mask */
#define RW 0x10 /* PTA4 mask */
#define EN 0x20 /* PTA5 mask */

void delayMs(int n);
void LCD_init(void);
void LCD_command(unsigned char command);
void LCD_data(unsigned char data);
void LCD_string(char cadena[]);

int main(void)
{
    __disable_irq();
    SIM->SCGC5 |= 0x400;
    SIM->SCGC5 |= 0x1000;
    PORTB->PCR[18] = 0x100;
    PORTB->PCR[19] = 0x100;
    PTB->PDDR |= 0xC0000;
    PORTD->PCR[1] = 0x100;
    PTD->PDDR |= 0x02;
    PTB->PDOR |= 0xC0000;
    PTD->PDOR |= 0x02;
    SIM->SCGC5 |= 0x200;

    /* configure PTA1 for interrupt */
    PORTA->PCR[1] |= 0x00100;
    PORTA->PCR[1] |= 0x00003;
    PTA->PDDR &= ~0x0002;
    PORTA->PCR[1] &= ~0xF0000;
    PORTA->PCR[1] |= 0xA0000;

    /* configure PTA13 for interrupt */
    PORTA->PCR[13] |= 0x00100;   /* make it GPIO */
    PORTA->PCR[13] |= 0x00003;   /* enable pull-up */
    PTA->PDDR &= ~0x2000;        /* bit 13 = 0x2000 */
    PORTA->PCR[13] &= ~0xF0000;  /* clear interrupt selection */
    PORTA->PCR[13] |= 0xA0000;   /* enable falling edge INT */

    NVIC->ISER[0] |= 0x40000000;
    __enable_irq();

    LCD_init();

    while(1)
    {
        PTB->PTOR |= 0x40000;   /* toggle red LED */
        delayMs(500);
    }
}

void PORTA_IRQHandler(void) {
    while (PORTA->ISFR & 0x00002002) {  /* bits 1 y 13 = 0x2002 */
        if (PORTA->ISFR & 0x00000002) {  /* PTA1 - bit 1 */
            LCD_string("Boton PTA1");
            delayMs(2500);
            LCD_command(0x01);
            PORTA->ISFR = 0x00000002;    /* clear PTA1 flag */
        }
        if (PORTA->ISFR & 0x00002000) {  /* PTA13 - bit 13 */
            LCD_string("Boton PTA13");
            delayMs(2500);
            LCD_command(0x01);
            PORTA->ISFR = 0x00002000;    /* clear PTA13 flag */
        }
    }
}

void LCD_init(void)
{
    SIM->SCGC5 |= 0x1000; /* Port D */
    PORTD->PCR[4] = 0x100;
    PORTD->PCR[5] = 0x100;
    PORTD->PCR[6] = 0x100;
    PORTD->PCR[7] = 0x100;
    PTD->PDDR = 0xFF;

    SIM->SCGC5 |= 0x0200; /* Port A */
    PORTA->PCR[2] = 0x100;
    PORTA->PCR[4] = 0x100;
    PORTA->PCR[5] = 0x100;
    PTA->PDDR |= 0x34;

    PTA->PCOR = RS | RW;
    delayMs(100);

    /* Secuencia de inicialización (modo 4 bits) */
    PTD->PDOR = (0x03 << 4);
    PTA->PSOR = EN; delayMs(1); PTA->PCOR = EN; delayMs(20);

    PTD->PDOR = (0x03 << 4);
    PTA->PSOR = EN; delayMs(1); PTA->PCOR = EN; delayMs(5);

    PTD->PDOR = (0x03 << 4);
    PTA->PSOR = EN; delayMs(1); PTA->PCOR = EN; delayMs(5);

    PTD->PDOR = (0x02 << 4);
    PTA->PSOR = EN; delayMs(1); PTA->PCOR = EN; delayMs(5);

    LCD_command(0x28); /* 4 bits, 2 líneas */
    LCD_command(0x06); /* cursor derecha */
    LCD_command(0x01); /* clear */
    delayMs(4);
    LCD_command(0x0F); /* display ON, cursor */
}

void LCD_command(unsigned char command)
{
    PTA->PCOR = RS | RW;

    PTD->PDOR = (PTD->PDOR & 0x0F) | ((command >> 4) << 4);
    PTA->PSOR = EN; delayMs(1); PTA->PCOR = EN;

    PTD->PDOR = (PTD->PDOR & 0x0F) | ((command & 0x0F) << 4);
    PTA->PSOR = EN; delayMs(1); PTA->PCOR = EN;

    if (command < 4) delayMs(4);
    else delayMs(1);
}

void LCD_data(unsigned char data)
{
    PTA->PSOR = RS;
    PTA->PCOR = RW;

    PTD->PDOR = (PTD->PDOR & 0x0F) | ((data >> 4) << 4);
    PTA->PSOR = EN; delayMs(1); PTA->PCOR = EN;

    PTD->PDOR = (PTD->PDOR & 0x0F) | ((data & 0x0F) << 4);
    PTA->PSOR = EN; delayMs(1); PTA->PCOR = EN;

    delayMs(1);
}

void LCD_string(char cadena[])
{
    int i = 0;
    while(cadena[i] != 0) {
        LCD_data(cadena[i]);
        i++;
    }
}

void delayMs(int n) {
    int i, j;
    for (i = 0; i < n; i++)
        for (j = 0; j < 7000; j++) { __asm("nop"); }
}

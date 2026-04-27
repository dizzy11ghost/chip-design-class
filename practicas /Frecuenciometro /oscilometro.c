// Mini challenge 6 Frecuenciómetro
// El objetivo de esta práctica es diseñar y construir un frecuencímetro
// utilizando los timers de un microcontrolador. Este dispositivo será capaz
// de medir la frecuencia de una señal de entrada con precisión (+-1%) y mostrar
// el resultado en una pantalla.
#include <MKL25Z4.H>

#define RS 0x04 /* PTA2 */
#define RW 0x10 /* PTA4 */
#define EN 0x20 /* PTA5 */

void init_TPM0(void);
void delayMs(int n);
void LCD_init(void);
void LCD_command(unsigned char command);
void LCD_data(unsigned char data);
void LCD_string(char cadena[]);

int main(void) {
	init_TPM0();
	PORTB->PCR[0] |= 0x03; // pull enable + pull-up
	uint16_t t1;
	uint16_t t2;
	int temp_t1 = 1;
	LCD_init();
	LCD_command(0x80);
	LCD_string("Frecuencia es: ");
	LCD_command(0xC0);
	int unidad, decena, centena, millar;
	unidad = 0;
	decena = 0;
	centena = 0;
	millar = 0;
	while(1){
		if (TPM0->CONTROLS[0].CnSC & 0x80){
			TPM0->CONTROLS[0].CnSC |= 0x80; // limpiar CHF
		    if (temp_t1) {
		    	t1 = TPM0->CONTROLS[0].CnV;  // primer flanco
		        temp_t1 = 0;
		    }
		    else{
		    	t2 = TPM0->CONTROLS[0].CnV;  // segundo flanco
		    	uint32_t ticks;
		    	if (t2 >= t1){
		    	    ticks = t2 - t1;
		    	}
		    	else{
		    	    ticks = (0xFFFF + 1 - t1 + t2);
		    	}
		    	float f = 8192.0f / ticks;
		    	int freq = (int)f;
		        millar = (freq / 1000) % 10;
		        centena = (freq / 100) % 10;
		        decena  = (freq / 10) % 10;
		        unidad  = freq % 10;
		        LCD_command(0xC0);
		        LCD_data(millar + '0');
		        LCD_data(centena + '0');
		        LCD_data(decena + '0');
		        LCD_data(unidad + '0');
		        LCD_data(' ');
		        LCD_data('H');
		        LCD_data('z');
		        LCD_data(' ');
		        temp_t1 = 1;
		        delayMs(300);
		    }
		}
	}
}

void init_TPM0(void){
	SIM->SCGC6  |= 0x01000000;   // clock a TPM0
	SIM->SOPT2  |= 0x03000000;   // fuente MCGIRCLK
	MCG->C2 |= 0x01;
	MCG->C1 |= 0x02;          // habilitar MCGIRCLK
	SIM->SCGC5 |= 0x0800       // clock Port B
	PORTC->PCR[1] = 0x400;       // MUX = ALT4 (TPM0_CH0)
	TPM0->SC  = 0;                 // detener
	TPM0->MOD = 0xFFFF;            // contador máximo
	TPM0->CNT = 0;
	TPM0->CONTROLS[0].CnSC = 0x14;
	TPM0->SC = 0x02;               // prescaler /4
	TPM0->SC |= 0x08;              /* enable timer free-running mode*/
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

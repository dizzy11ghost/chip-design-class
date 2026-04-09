//Práctica 1. Menú de LEDs
#include <MKL25Z4.h>
#define RS 0x04 /* PTA2 mask */
#define RW 0x10 /* PTA4 mask */
#define EN 0x20 /* PTA5 mask */

void delayMs(int n);
void delayUs(int n);

void keypad_init(void);
char keypad_getkey(void);
char get_key_pressed(void); //debouncer
void LCD_string(char cadena[]);
void LED_init(void);
void LED_set(int value);

void LCD_init(void);
void LCD_command (unsigned char command);
void LCD_data(unsigned char data);
void show_menu(void);
void menu(void);

//Hay que mapear los números de 1-16 a los valores del keypad
const char keymap[16] = {
    '1','2','3','A',
    '4','5','6','B',
    '7','8','9','C',
    '*','0','#','D'
};

char get_key_pressed(void){
	int code;
	while (keypad_getkey() != 0) { }   /* esperar a que se suelte cualquier tecla */
	delayMs(20);
	do {
        code = keypad_getkey();
	} while (code == 0);
	delayMs(20);                        /* debounce */
	return keymap[code - 1];            /* convertir 1-16 a caracter */

}

int main(void)
{
	/* Init code */
	SIM->SCGC6 |= 0x01000000; /* enable clock to TPM0 */
	SIM->SOPT2 |= 0x01000000; /* use 32.76khz as clock */
	TPM0->SC = 0; /* disable timer while configuring */
	TPM0->SC = 0x02; /* prescaler /4 */
	TPM0->MOD = 0x2000; /* max modulo value 8192*/
	TPM0->SC |= 0x80; /* clear TOF */
	TPM0->SC |= 0x08; /* enable timer free-running mode */

	keypad_init();
	LED_init();
	LCD_init();
	while(1){
		LCD_command(0x01); //clear
		delayMs(2);
		LCD_command(0x80);
		char key = get_key_pressed(); //debouncer del teclado
		if (key == 'A'){
			menu();
		}
	}
}

/* Initializes PortC that is connected to the keypad.
  Pins as GPIO input pin with pullup enabled.*/

void keypad_init(void)
{
	SIM->SCGC5 |= 0x0800;  /* enable clock to Port C */
	PORTC->PCR[0] = 0x103; /* PTD0, GPIO, enable pullup*/
	PORTC->PCR[1] = 0x103; /* PTD1, GPIO, enable pullup*/
	PORTC->PCR[2] = 0x103; /* PTD2, GPIO, enable pullup*/
	PORTC->PCR[3] = 0x103; /* PTD3, GPIO, enable pullup*/
	PORTC->PCR[4] = 0x103; /* PTD4, GPIO, enable pullup*/
	PORTC->PCR[5] = 0x103; /* PTD5, GPIO, enable pullup*/
	PORTC->PCR[6] = 0x103; /* PTD6, GPIO, enable pullup*/
	PORTC->PCR[7] = 0x103; /* PTD7, GPIO, enable pullup*/
	PTC->PDDR = 0x0F; /* make PTD7-0 as input pins */
}

/* keypad_getkey()
 * If a key is pressed, it returns a key code. Otherwise, a zero is returned.
The upper nibble of Port C is used as input. Pull-ups are enabled when the keys are not pressed
 * The lower nibble of Port C is used as output that drives the keypad rows.
 * First all rows are driven low and the input pins are read. If no key is pressed, it will read as all ones. Otherwise, some key is pressed.
 * If any key is pressed, the program drives one row low at a time and leave the rest of the rows inactive (float) then read the input pins.
 * Knowing which row is active and which column is active, the program can decide which key is pressed. */

char keypad_getkey(void) {

	int row, col;
	const char row_select[] = {0x01, 0x02, 0x04, 0x08};
	/* one row is active */
	/* check to see any key pressed */

	PTC->PDDR |= 0x0F; /* enable all rows */
	PTC->PCOR = 0x0F;
	delayUs(2); /* wait for signal return */
	col = PTC-> PDIR & 0xF0; /* read all columns */
	PTC->PDDR = 0; /* disable all rows */
	if (col == 0xF0)
		return 0; /* no key pressed */

	/* If a key is pressed, we need find out which key.*/
	for (row = 0; row < 4; row++)
	{ PTC->PDDR = 0; /* disable all rows */

	PTC->PDDR |= row_select[row]; /* enable one row */
	PTC->PCOR = row_select[row]; /* drive active row low*/

	delayUs(2); /* wait for signal to settle */
	col = PTC->PDIR & 0xF0; /* read all columns */

	if (col != 0xF0) break;
	/* if one of the input is low, some key is pressed. */
	}

	PTC->PDDR = 0; /* disable all rows */

	if (row == 4)
		return 0; /* if we get here, no key is pressed */

	/* gets here when one of the rows has key pressed*/
	//check which column it is/

	if (col == 0xE0) return row*4+ 1; /* key in column 0 */
	if (col == 0xD0) return row*4+ 2; /* key in column 1 */
	if (col == 0xB0) return row*4+ 3; /* key in column 2 */
	if (col == 0x70) return row*4+ 4; /* key in column 3 */
	return 0; /* just to be safe */
}

/* initialize all three LEDs on the FRDM board */
void LED_init(void)
{
	SIM->SCGC5 |= 0x400; /* enable clock to Port B */
	SIM->SCGC5 |= 0x1000; /* enable clock to Port D */
	PORTB->PCR[18] = 0x100; /* make PTB18 pin as GPIO */
	PTB->PDDR |= 0x40000; /* make PTB18 as output pin */
	PTB->PSOR |= 0x40000; /* turn off red LED */
	PORTB->PCR[19] = 0x100; /* make PTB19 pin as GPIO */
	PTB->PDDR |= 0x80000; /* make PTB19 as output pin */
	PTB->PSOR |= 0x80000; /* turn off green LED */
	PORTD->PCR[1] = 0x100; /* make PTD1 pin as GPIO */
	PTD->PDDR |= 0x02; /* make PTD1 as output pin */
	PTD->PSOR |= 0x02; /* turn off blue LED */
}

/* turn on or off the LEDs wrt to bit 2-0 of the value */
void LED_set(int value)
{
	/* use bit 0 of value to control red LED */
	if (value & 1)
		PTB->PCOR = 0x40000; else /* turn on red LED */
			PTB->PSOR = 0x40000; /* turn off red LED */
	/* use bit 1 of value to control green LED */
	if (value & 2)
		PTB->PCOR = 0x80000; else /* turn on green LED */
			PTB->PSOR = 0x80000; /* turn off green LED */
	/* use bit 2 of value to control blue LED */
	if (value & 4)
		PTD->PCOR = 0x02; else /* turn on blue LED */
			PTD->PSOR = 0x02; /* turn off blue LED */
}

/* Delay function */
void delayUs(int n) {
	while((TPM0->SC & 0x80) == 0) { }
	/* wait until the TOF is set */
	TPM0->SC |= 0x80; /* clear TOF */
}

//LCD stuff -------------------------------------------------------------------

void LCD_init(void)
{
	SIM->SCGC5 |= 0x1000; /* enable clock to Port D */
	//PORTD->PCR[0] = 0x100; /* make PTD0 pin as GPIO */
	//PORTD->PCR[1] = 0x100; /* make PTD1 pin as GPIO */
	//PORTD->PCR[2] = 0x100; /* make PTD1 pin as GPIO */
	//PORTD->PCR[3] = 0x100; /* make PTD1 pin as GPIO */
	PORTD->PCR[4] = 0x100; /* make PTD1 pin as GPIO */
	PORTD->PCR[5] = 0x100; /* make PTD1 pin as GPIO */
	PORTD->PCR[6] = 0x100; /* make PTD6 pin as GPIO */
	PORTD->PCR[7] = 0x100; /* make PTD7 pin as GPIO */
	PTD->PDDR = 0xFF; /* make PTD7-0 as output pins */
	SIM->SCGC5 |= 0x0200; /* enable clock to Port A */
	PORTA->PCR[2] = 0x100; /* make PTA2 pin as GPIO */
	PORTA->PCR[4] = 0x100; /* make PTA4 pin as GPIO */
	PORTA->PCR[5] = 0x100; /* make PTA5 pin as GPIO */
	PTA->PDDR |= 0x34; /* make PTA5, 4, 2 as out pins*/
	/* Initialization sequence for 4-bit mode */
	PTA->PCOR = RS | RW;
	delayMs(100);
	PTD->PDOR = (PTD->PDOR & 0x0F) | (0x03 << 4);
	PTA->PSOR = EN;
	delayMs(1);
	PTA->PCOR = EN;
	delayMs(20);

	PTD->PDOR = (PTD->PDOR & 0x0F) | (0x03 << 4);
	PTA->PSOR = EN;
	delayMs(1);
	PTA->PCOR = EN;
	delayMs(5);

	PTD->PDOR = (PTD->PDOR & 0x0F) | (0x03 << 4);
	PTA->PSOR = EN;
	delayMs(1);
	PTA->PCOR = EN;
	delayMs(5);

	PTD->PDOR = (PTD->PDOR & 0x0F) | (0x02 << 4);
	PTA->PSOR = EN;
	delayMs(1);
	PTA->PCOR = EN;
	delayMs(5);

	LCD_command(0x28);
	LCD_command(0x06);  /* move cursor right */
	LCD_command(0x01);  /* clear screen */
	delayMs(4);
	LCD_command(0x0F);  /* display on, cursor blinking */
}

void LCD_command(unsigned char command)
{
	PTA->PCOR = RS | RW; /* RS = 0, R/W = 0 */
	PTD->PDOR = (PTD->PDOR & 0x0F) | ((command >> 4) << 4); // mandar más significativo
	PTA->PSOR = EN; /* pulse E */
	delayMs(1);
	PTA->PCOR = EN; /* pulse E */
	PTD->PDOR = (PTD->PDOR & 0x0F) | ((command & 0x0F) << 4); // mandar menos significativo
	PTA->PSOR = EN; /* pulse E */
	delayMs(1);
	PTA->PCOR = EN;
	delayMs(1);
	if (command < 4)
		delayMs(4); /* command 1 and 2 needs up to 1.64ms */
	else
		delayMs(1); /* all others 40 us */
}
void LCD_data(unsigned char data)
{
	PTA->PSOR = RS; /* RS = 1, R/W = 0 */
	PTA->PCOR = RW;
	PTD->PDOR = (PTD->PDOR & 0x0F) | ((data >> 4) << 4); // mandar más significativo
	PTA->PSOR = EN; /* pulse E */
	delayMs(1);
	PTA->PCOR = EN; /* pulse E */
	PTD->PDOR = (PTD->PDOR & 0x0F) | ((data & 0x0F) << 4); // mandar menos significativo
	PTA->PSOR = EN; /* pulse E */
	delayMs(1);
	PTA->PCOR = EN; /* pulse E */
	delayMs(1);
}
/* Delay function */
void delayMs(int n) {
    for(int i = 0; i < n; i++) {
        while((TPM0->SC & 0x80) == 0) { }
        TPM0->SC |= 0x80;
    }
}
//para poner cadenas
void LCD_string(char cadena[]) {
    int i = 0;
    while(cadena[i] != 0) {
        LCD_data(cadena[i]);
        i++;
    }
}

void show_menu(){

	    LCD_command(0x01);
	    LCD_command(0x80);
	    LCD_string("1.Rojo 2.Naranja");
	    LCD_command(0xC0);
	    LCD_string("3.Amarillo");
	    delayMs(1500);

	    LCD_command(0x01);
	    LCD_command(0x80);
	    LCD_string("4.Verde 5.Cian");
	    LCD_command(0xC0);
	    LCD_string("6.Azul 7.Magenta");
	    delayMs(1500);

	    LCD_command(0x01);
	    LCD_command(0x80);
	    LCD_string("8.Blanco");
	    LCD_command(0xC0);
	    LCD_string("*=OK  A=Salir");
	    delayMs(1500);

	}

void menu(void)
{
    char selected = 0;
    char key;

    show_menu();

    while (1) {
        key = get_key_pressed();

        if (key == '*' && selected != 0) {
            LCD_command(0x01);
            delayMs(2);
            LCD_command(0x80);
            LCD_string("Tu seleccion:");
            LCD_command(0xC0);
            LCD_data(selected);

            switch (selected) {
                case '1': LED_set(1); break; /* rojo */
                case '2': LED_set(3); break; /* rojo + verde = naranja aprox. */
                case '3': LED_set(3); break; /* rojo + verde = amarillo aprox. */
                case '4': LED_set(2); break; /* verde */
                case '5': LED_set(6); break; /* verde + azul = cian */
                case '6': LED_set(4); break; /* azul */
                default:  LED_set(0); break;
            }

            delayMs(2000);
            selected = 0;
            show_menu();
            continue;
        }

        if (key == 'A') {
            LCD_command(0x01);
            delayMs(2);
            LCD_command(0x80);
            LCD_string("Saliendo...");
            LED_set(0);
            return;
        }

        /* Guardar seleccion si es 1-6 */
        if (key >= '1' && key <= '6') {
            selected = key;
            LCD_command(0xCF); /* ultima posicion linea 2 */
            LCD_data(selected);
        }
    }
}

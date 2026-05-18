#include <MKL25Z4.H>
#define RS 0x04 /* PTA2 mask */
#define RW 0x10 /* PTA4 mask */
#define EN 0x20 /* PTA5 mask */

void init_interrupt(void);
void show_menu();
void menu(void);
void delayMs(int n);
void delayUs(int n);
void keypad_init(void);
char keypad_getkey(void);
char get_key_pressed(void); //debouncer
void LCD_string(char cadena[]);
void LCD_init(void);
void LCD_command (unsigned char command);
void LCD_data(unsigned char data);
void ADC0_init(void);
unsigned short ADC0_read(void);
void show_menu(void);
void menu(void);
void PWM_motor_init(void);
void pwm_change(int numero);
void PWM_UpdateWidth(int pulseWidth);
void manual_mode(void);

volatile int motor_running = 1;  // el ISR de PTA13 la pone en 0
volatile int change_mode  = 0;   // el ISR de PTA16 la pone en 1

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

int main(void) {
    // init TPM0 para delays (igual que práctica 1)
    SIM->SCGC6 |= 0x01000000;
    SIM->SOPT2 |= 0x01000000;
    TPM0->SC = 0x02;
    TPM0->MOD = 0x2000;
    TPM0->SC |= 0x88;

    keypad_init();
    LCD_init();
    ADC0_init();
    PWM_motor_init();
    init_interrupt();
    menu();
    while(1){}
}

void PORTA_IRQHandler(void) {
    if (PORTA->ISFR & (1 << 13)) {   // botón STOP
        PORTA->ISFR = (1 << 13);
        motor_running = 0;
        pwm_change(0);               // apagar motor inmediatamente
    }
    if (PORTA->ISFR & (1 << 16)) {   // botón CAMBIAR MODO
        PORTA->ISFR = (1 << 16);
        change_mode = 1;
    }
}

void init_interrupt(void){
	__disable_irq(); /* disable all IRQs */
	SIM->SCGC5 |= 0x200; /* enable clock to Port A */
	/* configure PTA16 for interrupt */
	PORTA->PCR[16] |= 0x00100; /* make it GPIO */
	PORTA->PCR[16] |= 0x00003; /* enable pull-up */
	PTA->PDDR &= ~(1 << 16); /* make pin input */
	PORTA->PCR[16] &= ~0xF0000; /* clear interrupt selection */
	PORTA->PCR[16] |= 0xA0000; /* enable falling edge INT */
	/* configure PTA13 for interrupt*/
	PORTA->PCR[13] |= 0x00100; /* make it GPIO */
	PORTA->PCR[13] |= 0x00003; /* enable pull-up */
	PTA->PDDR &= ~(1 << 13); /* make pin input */
	PORTA->PCR[13] &= ~0xF0000; /* clear interrupt selection */
	PORTA->PCR[13] |= 0xA0000; /* enable falling edge INT */
	NVIC->ISER[0] |= 0x40000000; /* enable INT30 (bit 30 of ISER[0]) */
	__enable_irq(); /* global enable IRQs */
}

void ADC0_init(void) {

	SIM->SCGC5 |= 0x2000; /* clock to PORTE */

	PORTE->PCR[20] = 0; /* PTE20 analog input */

	SIM->SCGC6 |= 0x8000000; /* clock to ADC0 */

	ADC0->SC2 &= ~0x40; /* software trigger */

	/* clock div by 4, long sample time, single ended 12 bit, bus clock */

	ADC0->CFG1 = 0x40 | 0x10 | 0x04 | 0x00;
}

unsigned short ADC0_read(void){
    ADC0->SC1[0] = 0;              /* start conversion channel 0 */

    while(!(ADC0->SC1[0] & 0x80)) {
    }                              /* wait COCO */

    return ADC0->R[0];             /* read result */
}

void show_menu(){
	    LCD_command(0x01);
	    LCD_command(0x80);
	    LCD_string("Set input mode");
	    LCD_command(0xC0);
	    LCD_string("1.M     2.A");
}

void manual_mode(void) {
    char key;
    motor_running = 1;
    change_mode = 0;
    LCD_command(0x01); delayMs(2);
    LCD_command(0x80); LCD_string("Select Speed");
    LCD_command(0xC0); LCD_string("1:L 2:M 3:MH 4:H");
    while (!change_mode && motor_running) {
        int code = keypad_getkey();
        if (code != 0) {
            delayMs(20);
            key = keymap[code - 1];
            while (keypad_getkey() != 0) {}
            switch (key) {
                case '1':
                    pwm_change(1);
                    LCD_command(0x01);
                    LCD_command(0x80); LCD_string("Speed: LOW");
                    break;
                case '2':
                    pwm_change(2);
                    LCD_command(0x01);
                    LCD_command(0x80); LCD_string("Speed: MED");
                    break;
                case '3':
                    pwm_change(3);
                    LCD_command(0x01);
                    LCD_command(0x80); LCD_string("Speed: MED-HI");
                    break;
                case '4':
                    pwm_change(4);
                    LCD_command(0x01);
                    LCD_command(0x80); LCD_string("Speed: HIGH");
                    break;
            }
        }
    }
    pwm_change(0);
}

void automatic_mode(void) {
    unsigned short adc_val;
    motor_running = 1;
    change_mode   = 0;
    LCD_command(0x01); delayMs(2);
    LCD_command(0x80); LCD_string("Auto Mode");
    LCD_command(0xC0); LCD_string("ADC->Speed");
    while (!change_mode && motor_running) {
        adc_val = ADC0_read();
        if (adc_val <= 930){
        	LCD_command(0x01);
        	LCD_command(0x80); LCD_string("Speed: LOW");
        	pwm_change(1);
        }
        else if (adc_val <= 1860){
        	LCD_command(0x01);
        	LCD_command(0x80); LCD_string("Speed: MED");
        	pwm_change(2);
        }
        else if (adc_val <= 2790){
        	LCD_command(0x01);
        	LCD_command(0x80); LCD_string("Speed: MED-HIGH");
        	pwm_change(3);
        }
        else{
        	LCD_command(0x01);
        	LCD_command(0x80); LCD_string("Speed: HIGH");
        	pwm_change(4);
        }
        delayMs(100);
    }
    pwm_change(0);
}

void menu(void) {
    char key;
    char selected = 0;
    while (1) {
        show_menu();
        selected = 0;
        while (selected == 0) {
            key = get_key_pressed();
            if (key == '1' || key == '2') {
                selected = key;
                LCD_command(0xC0);
                if(key == '1'){
                	LCD_string("Sel: Manual");
                }
                else{
                	LCD_string("Sel: Auto");
                }
            }
            if (key == '#' && selected != 0) break;
        }
        if (key != '#') {
            while (get_key_pressed() != '#') {}
        }
        if (selected == '1')
        	manual_mode();
        else
        	automatic_mode();
        if (!motor_running) {
            LCD_command(0x01); delayMs(2);
            LCD_command(0x80); LCD_string("Motor stopped");
            LCD_command(0xC0); LCD_string("Press any key");
            get_key_pressed(); /* esperar antes de volver al menú */
        }
    }
}

void PWM_motor_init(void){
    /* Clock Port A */
    SIM->SCGC5 |= 0x0200;
    /* PTA1 -> TPM2_CH0 (ALT3) */
    PORTA->PCR[1] = 0x0300;
    /* Clock TPM2 */
    SIM->SCGC6 |= 0x04000000;
    /* TPM clock = MCGFLLCLK */
    SIM->SOPT2 |= 0x01000000;
    /* Disable TPM2 */
    TPM2->SC = 0;
    /* Edge-aligned PWM, high-true pulses */
    TPM2->CONTROLS[0].CnSC = 0x28;
    /* PWM frequency */
    TPM2->MOD = 43702;
    /* Start TPM2 prescaler /16 */
    TPM2->SC = 0x0C;
    /* Start with 0% duty */
    TPM2->CONTROLS[0].CnV = 0;
}

void pwm_change(int numero)
{
    switch(numero)
    {
        case 0:
            TPM2->CONTROLS[0].CnV = 0;
            break;

        case 1:
            TPM2->CONTROLS[0].CnV = 10925;
            break;

        case 2:
            TPM2->CONTROLS[0].CnV = 21851;
            break;

        case 3:
            TPM2->CONTROLS[0].CnV = 32777;
            break;

        case 4:
            TPM2->CONTROLS[0].CnV = 43702;
            break;

        default:
            TPM2->CONTROLS[0].CnV = 0;
            break;
    }
}

void PWM_UpdateWidth(int pulseWidth){
	if (pulseWidth <= 43702) {
			TPM2->CONTROLS[0].CnV = pulseWidth;
	    }
}

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
/* Delay function */
void delayUs(int n) {
	while((TPM0->SC & 0x80) == 0) { }
	/* wait until the TOF is set */
	TPM0->SC |= 0x80; /* clear TOF */
}

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

void LCD_command(unsigned char command){
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

void delayMs(int n) {
    for(int i = 0; i < n; i++) {
        while((TPM0->SC & 0x80) == 0) { }
        TPM0->SC |= 0x80;
    }
}

void LCD_string(char cadena[]) {
    int i = 0;
    while(cadena[i] != 0) {
        LCD_data(cadena[i]);
        i++;
    }
}

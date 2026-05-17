#include <MKL25Z4.h>

#define RS 0x04
#define RW 0x10
#define EN 0x20

void delayMs(int n);
void delayUs(int n);

void keypad_init(void);
char keypad_getkey(void);
char get_key_pressed(void);

void LCD_init(void);
void LCD_command(unsigned char command);
void LCD_data(unsigned char data);
void LCD_string(char cadena[]);

void LED_init(void);
void LED_set(int value);

void show_menu(void);
void handle_key(char key);

//mapeo de las teclas a caracteres
const char keymap[16] = {
    '1','2','3','A',
    '4','5','6','B',
    '7','8','9','C',
    '*','0','#','D'
};

//main
int main(void)
{
    SIM->SCGC6 |= 0x01000000;
    SIM->SOPT2 |= 0x01000000;
    TPM0->SC    = 0;
    TPM0->SC    = 0x02;
    TPM0->MOD   = 0x2000;
    TPM0->SC   |= 0x80;
    TPM0->SC   |= 0x08;

    keypad_init();
    LCD_init();
    LED_init();

    show_menu();

    while (1) {
        char key = get_key_pressed();
        handle_key(key); //para ignorar todo lo que no sea 1, 2 o 3
    }
}

//menu
void show_menu(void)
{
    LCD_command(0x01);
    delayMs(2);
    LCD_command(0x80);
    LCD_string("PRESS BUTTON");
    LCD_command(0xC0);
    LCD_string("R:1  B:2  G:3");
}
//vemos la tecla
void handle_key(char key)
{
    char *color_name;
    int   led_value;

    switch (key) {
        case '1': color_name = "RED";   led_value = 1; break;
        case '2': color_name = "BLUE";  led_value = 4; break;
        case '3': color_name = "GREEN"; led_value = 2; break;
        default:  return; 
    }

    LED_set(led_value);

    LCD_command(0x01);
    delayMs(2);
    LCD_command(0x80);
    LCD_string(color_name);

    LCD_command(0xC0);
    LCD_string("LED IS ON!");

    delayMs(3000); //delay 3 segundos

   //apaga el LED y regresa al menú
    LED_set(0);
    show_menu();
}

//debouncer
char get_key_pressed(void)
{
    int code;
    while (keypad_getkey() != 0) { }
    delayMs(20);
    do {
        code = keypad_getkey();
    } while (code == 0);
    delayMs(20);//debounce
    return keymap[code - 1];
}

//Keypad
void keypad_init(void)
{
    SIM->SCGC5    |= 0x0800;
    PORTC->PCR[0]  = 0x103;
    PORTC->PCR[1]  = 0x103;
    PORTC->PCR[2]  = 0x103;
    PORTC->PCR[3]  = 0x103;
    PORTC->PCR[4]  = 0x103;
    PORTC->PCR[5]  = 0x103;
    PORTC->PCR[6]  = 0x103;
    PORTC->PCR[7]  = 0x103;
    PTC->PDDR      = 0x0F;
}

char keypad_getkey(void)
{
    int row, col;
    const char row_select[] = {0x01, 0x02, 0x04, 0x08};

    PTC->PDDR |= 0x0F;
    PTC->PCOR  = 0x0F;
    delayUs(2);
    col = PTC->PDIR & 0xF0;
    PTC->PDDR  = 0;
    if (col == 0xF0) return 0;

    for (row = 0; row < 4; row++) {
        PTC->PDDR  = 0;
        PTC->PDDR |= row_select[row];
        PTC->PCOR  = row_select[row];
        delayUs(2);
        col = PTC->PDIR & 0xF0;
        if (col != 0xF0) break;
    }
    PTC->PDDR = 0;

    if (row == 4)   return 0;
    if (col == 0xE0) return row * 4 + 1;
    if (col == 0xD0) return row * 4 + 2;
    if (col == 0xB0) return row * 4 + 3;
    if (col == 0x70) return row * 4 + 4;
    return 0;
}

//LEDs
void LED_init(void)
{
    SIM->SCGC5     |= 0x400;
    SIM->SCGC5     |= 0x1000;
    PORTB->PCR[18]  = 0x100;
    PTB->PDDR      |= 0x40000;
    PTB->PSOR      |= 0x40000;
    PORTB->PCR[19]  = 0x100;
    PTB->PDDR      |= 0x80000;
    PTB->PSOR      |= 0x80000;
    PORTD->PCR[1]   = 0x100;
    PTD->PDDR      |= 0x02;
    PTD->PSOR      |= 0x02;
}

void LED_set(int value)
{
    if (value & 1) PTB->PCOR = 0x40000; else PTB->PSOR = 0x40000; /* rojo  */
    if (value & 2) PTB->PCOR = 0x80000; else PTB->PSOR = 0x80000; /* verde */
    if (value & 4) PTD->PCOR = 0x02;    else PTD->PSOR = 0x02;    /* azul  */
}

//LCD
void LCD_init(void)
{
    SIM->SCGC5     |= 0x1000;
    PORTD->PCR[4]   = 0x100;
    PORTD->PCR[5]   = 0x100;
    PORTD->PCR[6]   = 0x100;
    PORTD->PCR[7]   = 0x100;
    PTD->PDDR       = 0xFF;
    SIM->SCGC5     |= 0x0200;
    PORTA->PCR[2]   = 0x100;
    PORTA->PCR[4]   = 0x100;
    PORTA->PCR[5]   = 0x100;
    PTA->PDDR      |= 0x34;

    PTA->PCOR = RS | RW;
    delayMs(100);

    PTD->PDOR = (PTD->PDOR & 0x0F) | (0x03 << 4);
    PTA->PSOR = EN; delayMs(1); PTA->PCOR = EN; delayMs(20);
    PTD->PDOR = (PTD->PDOR & 0x0F) | (0x03 << 4);
    PTA->PSOR = EN; delayMs(1); PTA->PCOR = EN; delayMs(5);
    PTD->PDOR = (PTD->PDOR & 0x0F) | (0x03 << 4);
    PTA->PSOR = EN; delayMs(1); PTA->PCOR = EN; delayMs(5);
    PTD->PDOR = (PTD->PDOR & 0x0F) | (0x02 << 4);
    PTA->PSOR = EN; delayMs(1); PTA->PCOR = EN; delayMs(5);

    LCD_command(0x28);
    LCD_command(0x06);
    LCD_command(0x01);
    delayMs(4);
    LCD_command(0x0C);   /* display on, cursor off */
}

void LCD_command(unsigned char command)
{
    PTA->PCOR = RS | RW;
    PTD->PDOR = (PTD->PDOR & 0x0F) | ((command >> 4) << 4);
    PTA->PSOR = EN; delayMs(1); PTA->PCOR = EN;
    PTD->PDOR = (PTD->PDOR & 0x0F) | ((command & 0x0F) << 4);
    PTA->PSOR = EN; delayMs(1); PTA->PCOR = EN;
    delayMs((command < 4) ? 4 : 1);
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
    while (cadena[i] != 0) { LCD_data(cadena[i]); i++; }
}

//delays
void delayMs(int n)
{
    for (int i = 0; i < n; i++) {
        while ((TPM0->SC & 0x80) == 0) { }
        TPM0->SC |= 0x80;
    }
}

void delayUs(int n)
{
    (void)n;                   /* resolución mínima = 1 tick TPM */
    while ((TPM0->SC & 0x80) == 0) { }
    TPM0->SC |= 0x80;
}

// 04. LCD-Keyboard-Timers-Interrupts ejercicio 3
#include <MKL25Z4.H>
#include <stdint.h>

#define RS 0x04
#define RW 0x10
#define EN 0x20

#define TIMER_CLOCK_HZ 32768UL

//Interrupt service routine --- main
volatile uint8_t paused = 0;   // 1 = pausado, 0 = contando
//volatile hace que el compilador no la optimice como constante!!

uint8_t  TPM0_set_period_seconds(uint8_t seconds);
void     delayMs(int n);
void     delayUs(int n);
void     LCD_init(void);
void     LCD_command(unsigned char command);
void     LCD_data(unsigned char data);
void     LCD_string(char cadena[]);
char     get_key_pressed(void);
void     keypad_init(void);
char     keypad_getkey(void);
uint8_t  leer_segundos(void);
void     PTA1_interrupt_init(void);

const char keymap[16] = { //mapeamos las teclas
    '1','2','3','A',
    '4','5','6','B',
    '7','8','9','C',
    '*','0','#','D'
};

//PORTA_IQRHandler se detiene el TPMO desactivando el bit CMOD
void PORTA_IRQHandler(void) {
    if (PORTA->ISFR & (1 << 1)) {// confirmar que fue PTA1

        // Detener el timer
        TPM0->SC &= ~0x08;// CMOD = 00: clock desactivado

        // Mostrar PAUSED en LCD
        LCD_command(0x80);
        LCD_string("PAUSED");
        LCD_command(0xC0);
        LCD_string("Presiona *      ");

        paused = 1;// señalar al main

        PORTA->ISFR = (1 << 1);// limpiamos la bandera de interrupción para evitar re-disparos
    }
}

int main(void) {
    LCD_init();
    keypad_init();

    // LED rojo (PTD1) para parpadeo al final
    SIM->SCGC5|= 0x1000;
    PORTD->PCR[1] = 0x100;
    PTD->PDDR |= 0x02;
    PTD->PSOR = 0x02;// apagado (activo-bajo)

    // interrupción en PTA1
    PTA1_interrupt_init();

    // Pantalla bienvenida
    LCD_command(0x80);
    LCD_string("Hello");
    delayMs(2000);

    // Le pedimos input al usuario
    LCD_command(0x01); delayMs(2);
    LCD_command(0x80);
    LCD_string("Tiempo (s):");

    uint8_t segundos = leer_segundos();
    if (segundos == 0) segundos = 1;

    // Timer de 1s
    TPM0_set_period_seconds(1);

    //Pantalla para contar
    LCD_command(0x01); delayMs(2);
    LCD_command(0x80);
    LCD_string("Contando...");

    // Mostrar "00s / XXs" en línea 2
    char lim[4];
    lim[0] = '0' + (segundos / 10);
    lim[1] = '0' + (segundos % 10);
    lim[2] = 's'; lim[3] = 0;

    LCD_command(0xC0);
    LCD_string("00s / ");
    LCD_string(lim);

    uint8_t cuenta = 0;
    char buf[4];

    while (1) {

        //Esperamos la tecla *
        if (paused) {
            char key = get_key_pressed();
            if (key == '*') {
                paused = 0;

                //para restaurar la pantalla de bloqueo
                LCD_command(0x01); delayMs(2);
                LCD_command(0x80);
                LCD_string("Contando...");

                // actualizamos línea 2 con el valor actual
                LCD_command(0xC0);
                buf[0] = '0' + (cuenta / 10);
                buf[1] = '0' + (cuenta % 10);
                buf[2] = 's'; buf[3] = 0;
                LCD_string(buf);
                LCD_string(" / ");
                LCD_string(lim);

                // Reanudar timer (CMOD = 01)
                TPM0->SC |= 0x08;
            }
            continue;// no procesar TOF (Time overflow flag) mientras está pausado
        }

        // tick del timer
        if (TPM0->SC & 0x80) {          // TOF set?
            TPM0->SC |= 0x80;           // limpiar TOF

            cuenta++;

            LCD_command(0xC0);
            buf[0] = '0' + (cuenta / 10);
            buf[1] = '0' + (cuenta % 10);
            buf[2] = 's'; buf[3] = 0;
            LCD_string(buf);

            if (cuenta >= segundos) { //límite en segundos
                TPM0->SC &= ~0x08; //detenemos timer

                LCD_command(0x01); delayMs(2);
                LCD_command(0x80);
                LCD_string("Tiempo cumplido!");

                int i;
                for (i = 0; i < 10; i++) {
                    PTD->PTOR = 0x02; //toggle LED
                    delayMs(300);
                }
                PTD->PSOR = 0x02;// apagar LED

                LCD_command(0xC0);
                LCD_string("FIN");
                while (1); // quedarse aquí
            }
        }
    }
}

// Interrupción en PTA1
void PTA1_interrupt_init(void) {
    __disable_irq();

    SIM->SCGC5   |= 0x0200;// clock para PORTA
    PORTA->PCR[1] = 0x103;// pull-up + GPIO (MUX=001)
    PTA->PDDR    &= ~(1 << 1);// PTA1 como entrada

    // Flanco de bajada (falling edge) → IRQ_CFG = 1010
    PORTA->PCR[1] &= ~0x000F0000;
    PORTA->PCR[1] |=  0x000A0000;

    NVIC->ISER[0] |= (1 << 30);// habilitar IRQ30 = PORTA

    __enable_irq();
}

// TPMO timer
uint8_t TPM0_set_period_seconds(uint8_t seconds) {
    if (seconds == 0 || seconds > 99) return 0;

    uint8_t  ps_bits = 0x07;
    uint32_t ps_div  = 128;
    uint32_t mod = (TIMER_CLOCK_HZ * (uint32_t)seconds) / ps_div - 1;

    SIM->SCGC6  |= 0x01000000;
    SIM->SOPT2  |= 0x03000000;
    MCG->C1     |= 0x02;

    TPM0->SC     = 0;
    TPM0->CNT    = 0;
    TPM0->MOD    = (uint16_t)mod;
    TPM0->SC     = ps_bits;
    TPM0->SC    |= 0x08; // CMOD=01: clock activo
    return 1;
}

//leemos los segundos desde el keypad
uint8_t leer_segundos(void) {
    uint8_t valor = 0;
    char key;
    LCD_command(0xC0);
    while (1) {
        key = get_key_pressed();
        if (key >= '0' && key <= '9') {
            if (valor < 10) {
                valor = valor * 10 + (key - '0');
                LCD_data(key);
            }
        }
        if (key == '*' || key == '#') break;
    }
    return valor;
}

//LCD
void LCD_init(void) {
    SIM->SCGC5 |= 0x1000;
    PORTD->PCR[4] = 0x100; PORTD->PCR[5] = 0x100;
    PORTD->PCR[6] = 0x100; PORTD->PCR[7] = 0x100;
    PTD->PDDR = 0xFF;
    SIM->SCGC5 |= 0x0200;
    PORTA->PCR[2] = 0x100; PORTA->PCR[4] = 0x100; PORTA->PCR[5] = 0x100;
    PTA->PDDR |= 0x34;
    PTA->PCOR = RS | RW;
    delayMs(100);
    PTD->PDOR = (0x03 << 4);
    PTA->PSOR = EN; delayMs(1); PTA->PCOR = EN; delayMs(20);
    PTD->PDOR = (0x03 << 4);
    PTA->PSOR = EN; delayMs(1); PTA->PCOR = EN; delayMs(5);
    PTD->PDOR = (0x03 << 4);
    PTA->PSOR = EN; delayMs(1); PTA->PCOR = EN; delayMs(5);
    PTD->PDOR = (0x02 << 4);
    PTA->PSOR = EN; delayMs(1); PTA->PCOR = EN; delayMs(5);
    LCD_command(0x28);
    LCD_command(0x06);
    LCD_command(0x01); delayMs(4);
    LCD_command(0x0F);
}

void LCD_command(unsigned char command) {
    PTA->PCOR = RS | RW;
    PTD->PDOR = (PTD->PDOR & 0x0F) | ((command >> 4) << 4);
    PTA->PSOR = EN; delayMs(1); PTA->PCOR = EN;
    PTD->PDOR = (PTD->PDOR & 0x0F) | ((command & 0x0F) << 4);
    PTA->PSOR = EN; delayMs(1); PTA->PCOR = EN;
    if (command < 4) delayMs(4);
    else             delayMs(1);
}

void LCD_data(unsigned char data) {
    PTA->PSOR = RS; PTA->PCOR = RW;
    PTD->PDOR = (PTD->PDOR & 0x0F) | ((data >> 4) << 4);
    PTA->PSOR = EN; delayMs(1); PTA->PCOR = EN;
    PTD->PDOR = (PTD->PDOR & 0x0F) | ((data & 0x0F) << 4);
    PTA->PSOR = EN; delayMs(1); PTA->PCOR = EN;
    delayMs(1);
}

void LCD_string(char cadena[]) {
    int i = 0;
    while (cadena[i] != 0) { LCD_data(cadena[i]); i++; }
}

//delays
void delayMs(int n) {
    int i, j;
    for (i = 0; i < n; i++)
        for (j = 0; j < 7000; j++) { __asm("nop"); }
}

void delayUs(int n) {
    int i, j;
    for (i = 0; i < n; i++)
        for (j = 0; j < 7; j++) { __asm("nop"); }
}
//Para el KeyPad
char get_key_pressed(void) {
    int code;
    while (keypad_getkey() != 0) { }
    delayMs(20);
    do { code = keypad_getkey(); } while (code == 0);
    delayMs(20);
    return keymap[code - 1];
}

void keypad_init(void) {
    SIM->SCGC5 |= 0x0800;
    PORTC->PCR[0] = 0x103; PORTC->PCR[1] = 0x103;
    PORTC->PCR[2] = 0x103; PORTC->PCR[3] = 0x103;
    PORTC->PCR[4] = 0x103; PORTC->PCR[5] = 0x103;
    PORTC->PCR[6] = 0x103; PORTC->PCR[7] = 0x103;
    PTC->PDDR = 0x0F;
}

char keypad_getkey(void) {
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
    if (row == 4)      return 0;
    if (col == 0xE0)   return row * 4 + 1;
    if (col == 0xD0)   return row * 4 + 2;
    if (col == 0xB0)   return row * 4 + 3;
    if (col == 0x70)   return row * 4 + 4;
    return 0;
}

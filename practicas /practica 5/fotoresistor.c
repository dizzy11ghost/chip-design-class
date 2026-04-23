#include <MKL25Z4.h>
#include <stdio.h>

/* Definiciones de la LCD (4 bits) */
#define RS 0x04 /* PTA2 mask */
#define RW 0x10 /* PTA4 mask */
#define EN 0x20 /* PTA5 mask */

/* --- CONFIGURACIÓN --- */
#define UMBRAL_DEFINIDO 75

/* Prototipos */
void delayMs(int n);
void LCD_init(void);
void LCD_command(unsigned char command);
void LCD_data(unsigned char data);
void LCD_string(char cadena[]);
void LED_init(void);
void ADC0_init(void);
unsigned short ADC0_read(void);

int main(void) {
    char buffer[20];
    unsigned short adc_raw;
    int nivel_luz;
    int tiempo_acumulado = 0; // Rastreador de milisegundos

    /* Reloj para TPM0 */
    SIM->SCGC6 |= 0x01000000;
    SIM->SOPT2 |= 0x01000000;
    TPM0->SC = 0;
    TPM0->SC = 0x02;
    TPM0->MOD = 0x2000;
    TPM0->SC |= 0x08;

    /* Inicializaciones */
    LED_init();
    ADC0_init();
    LCD_init();

    // ETAPA 1: Sensibilidad inicial (5 segundos)
    LCD_command(0x01);
    LCD_string("Sensibilidad");
    LCD_command(0xC0);
    sprintf(buffer, "Nivel: %d", UMBRAL_DEFINIDO);
    LCD_string(buffer);
    delayMs(3000);

    // ETAPA 2: Monitoreo Activo
    while(1) {
        // 1. LEER ADC SIEMPRE
        adc_raw = ADC0_read();
        nivel_luz = (adc_raw * 100) / 4095;

        // 2. ACTUALIZAR LCD SIEMPRE (Sin borrar pantalla para evitar parpadeo)
        LCD_command(0x80); // Posición inicial
        if (nivel_luz <= UMBRAL_DEFINIDO) {
            LCD_string("Luz: ENCENDIDA "); // Espacios para limpiar
        } else {
            LCD_string("Luz: APAGADA   ");
        }

        LCD_command(0xC0); // Segunda línea
        sprintf(buffer, "Nivel: %d%%      ", nivel_luz);
        LCD_string(buffer);

        // 3. CONTROL DE TIEMPO DEL LED
        // Esperamos 100ms en cada vuelta para que el monitoreo sea rápido
        delayMs(100);
        tiempo_acumulado += 175;

        // Si ya pasaron 2000ms (2 segundos), actualizamos el LED
        if (tiempo_acumulado >= 2000) {
            if (nivel_luz <= UMBRAL_DEFINIDO) {
                PTB->PCOR = (1 << 19); // ON
            } else {
                PTB->PSOR = (1 << 19); // OFF
            }
            tiempo_acumulado = 0; // Reiniciar contador
        }
    }
}

/* --- PERIFÉRICOS --- */

void ADC0_init(void) {
    SIM->SCGC6 |= SIM_SCGC6_ADC0_MASK;
    SIM->SCGC5 |= SIM_SCGC5_PORTE_MASK;
    PORTE->PCR[20] &= ~0x703; // Modo analógico puro
    ADC0->CFG1 = 0x04; // 12-bit
    ADC0->SC1[0] = 0x1F;
}

unsigned short ADC0_read(void) {
    ADC0->SC1[0] = 0;
    while(!(ADC0->SC1[0] & ADC_SC1_COCO_MASK));
    return (unsigned short)ADC0->R[0];
}

void LED_init(void) {
    SIM->SCGC5 |= SIM_SCGC5_PORTB_MASK;
    PORTB->PCR[19] = 0x100;
    PTB->PDDR |= (1 << 19);
    PTB->PSOR |= (1 << 19); // Apagado
}

void LCD_init(void) {
    SIM->SCGC5 |= 0x1000;
    PORTD->PCR[4] = 0x100; PORTD->PCR[5] = 0x100;
    PORTD->PCR[6] = 0x100; PORTD->PCR[7] = 0x100;
    PTD->PDDR |= 0xF0;
    SIM->SCGC5 |= 0x0200;
    PORTA->PCR[2] = 0x100; PORTA->PCR[4] = 0x100; PORTA->PCR[5] = 0x100;
    PTA->PDDR |= 0x34;

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
    LCD_command(0x0C);
}

void LCD_command(unsigned char command) {
    PTA->PCOR = RS | RW;
    PTD->PDOR = (PTD->PDOR & 0x0F) | (command & 0xF0);
    PTA->PSOR = EN; delayMs(1); PTA->PCOR = EN;
    PTD->PDOR = (PTD->PDOR & 0x0F) | ((command & 0x0F) << 4);
    PTA->PSOR = EN; delayMs(1); PTA->PCOR = EN;
    delayMs(2);
}

void LCD_data(unsigned char data) {
    PTA->PSOR = RS; PTA->PCOR = RW;
    PTD->PDOR = (PTD->PDOR & 0x0F) | (data & 0xF0);
    PTA->PSOR = EN; delayMs(1); PTA->PCOR = EN;
    PTD->PDOR = (PTD->PDOR & 0x0F) | ((data & 0x0F) << 4);
    PTA->PSOR = EN; delayMs(1); PTA->PCOR = EN;
    delayMs(1);
}

void LCD_string(char cadena[]) {
    int i = 0;
    while(cadena[i] != 0) {
        LCD_data(cadena[i]);
        i++;
    }
}

void delayMs(int n) {
    for(int i = 0; i < n; i++) {
        while((TPM0->SC & 0x80) == 0) { }
        TPM0->SC |= 0x80;
    }
}

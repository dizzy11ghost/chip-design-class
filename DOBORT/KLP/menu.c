#include <MKL25Z4.h>
#include "FreeRTOS.h"
#include "task.h"
#include "queue.h"
#include "semphr.h"
#include "board.h"
#include "pin_mux.h"

#define RS 0x04
#define RW 0x10
#define EN 0x20

QueueHandle_t uart_queue;
SemaphoreHandle_t sem_emergencia;

const char keymap[16] = {
    '1','2','3','A',
    '4','5','6','B',
    '7','8','9','C',
    '*','0','#','D'
};

void TPM0_init(void);
void delayMs(int n);
void delayUs(int n);
void keypad_init(void);
char keypad_getkey(void);
char get_key_pressed(void);
void LCD_init(void);
void LCD_command(unsigned char command);
void LCD_data(unsigned char data);
void LCD_string(char cadena[]);
void UART1_init(uint32_t baud);
void UART1_send_char(char c);
void pantalla_bienvenida(void);
void menu_principal(void);
void flujo_mandar(void);
void flujo_recibir(void);

void PORTA_IRQHandler(void){
	if(PORTA->ISFR & (1 << 13)){
		PORTA->ISFR = (1 << 13);
		BaseType_t xWoken = pdFALSE;
		xSemaphoreGiveFromISR(sem_emergencia, &xWoken);
		portYIELD_FROM_ISR(xWoken);
	}
}

void tarea_emergencia(void *pv){
	while(1){
		xSemaphoreTake(sem_emergencia, portMAX_DELAY);
		LCD_command(0x01);
		delayMs(4);
		LCD_command(0x80);
		LCD_string("Emergencia");
		LCD_command(0xC0);
		LCD_string("Sistema detenido");
		while(1){}
	}
}

void tarea_uart_rx(void *pv){
	while(1){
		while(!(UART1->S1 & UART_S1_RDRF_MASK)){
			vTaskDelay(pdMS_TO_TICKS(1));
		}
		char c = UART1->D;
		xQueueSend(uart_queue, &c, portMAX_DELAY);
	}
}

void tarea_ui(void *pv){
	pantalla_bienvenida();
	while(1){
		menu_principal();
	}
}

int main(void){
	BOARD_InitBootClocks();
	BOARD_InitPins();
	TPM0_init();
	UART1_init(9600);
	LCD_init();
	keypad_init();
	uart_queue = xQueueCreate(10, sizeof(char));
	sem_emergencia =  xSemaphoreCreateBinary();
	xTaskCreate(tarea_emergencia, "EMG", 256, NULL, 3, NULL);
	xTaskCreate(tarea_uart_rx, "URX", 256, NULL, 2, NULL);
	xTaskCreate(tarea_ui, "UI", 512, NULL, 1, NULL);
	vTaskStartScheduler();
	while(1){}
}

void pantalla_bienvenida(void) {
    LCD_command(0x01);
    delayMs(4);
    LCD_command(0x80);
    LCD_string("    DOBOT     ");
    LCD_command(0xC0);
    LCD_string("  Bienvenido  ");
    delayMs(3000);
}

void menu_principal(void) {
    LCD_command(0x01);
    delayMs(4);
    LCD_command(0x80);
    LCD_string("  Selecciona:  ");
    LCD_command(0xC0);
    LCD_string("1.Mandar 2.Recib");
    char tecla = 0;
    while (tecla != '1' && tecla != '2') {
        int code = keypad_getkey();
        if (code != 0) {
            delayMs(20);
            tecla = keymap[code - 1];
            while (keypad_getkey() != 0) {}
        }
        vTaskDelay(pdMS_TO_TICKS(10));
    }
    if (tecla == '1')
    	flujo_mandar();
    else
    	flujo_recibir();
}

void flujo_mandar(void) {
    LCD_command(0x01);
    delayMs(4);
    LCD_command(0x80);
    LCD_string("Coloca paquete");
    LCD_command(0xC0);
    LCD_string("1. Ya lo puse");
    char tecla = 0;
    while (tecla != '1') {
    	if (tecla == '#') return;
        int code = keypad_getkey();
        if (code != 0) {
            delayMs(20);
            tecla = keymap[code - 1];
            while (keypad_getkey() != 0) {}
        }
        vTaskDelay(pdMS_TO_TICKS(10));
    }
    UART1_send_char('R');
    UART1_send_char('S');
    LCD_command(0x01);
    delayMs(4);
    LCD_command(0x80);
    LCD_string("Esperando...");
    LCD_command(0xC0);
    LCD_string("Depositando");
    char dest, dato;
    while (1) {
        xQueueReceive(uart_queue, &dest, portMAX_DELAY);
        xQueueReceive(uart_queue, &dato, portMAX_DELAY);
        if (dest == 'M' && dato == 'E') {
            LCD_command(0x01);
            delayMs(4);
            LCD_command(0x80);
            LCD_string("Estante lleno");
            delayMs(2000);
            return;
        } else if (dest == 'M' && dato == 'L') {
            LCD_command(0x01);
            delayMs(4);
            LCD_command(0x80);
            LCD_string("Paquete listo");
            LCD_command(0xC0);
            LCD_string("Depositado OK");
            delayMs(2000);
            return;
        }
    }
}

void flujo_recibir(void) {
    while (1) {
        LCD_command(0x01);
        delayMs(4);
        LCD_command(0x80);
        LCD_string("Selec. espacio:");
        LCD_command(0xC0);
        LCD_string("1-6: FT1-FT6");
        char tecla = 0;
        while (tecla < '1' || tecla > '6') {
        	if (tecla == '#') return;
            int code = keypad_getkey();
            if (code != 0) {
                delayMs(20);
                tecla = keymap[code - 1];
                while (keypad_getkey() != 0) {}
            }
            vTaskDelay(pdMS_TO_TICKS(10));
        }
        UART1_send_char('R');
        UART1_send_char(tecla);
        char dest, dato;
        xQueueReceive(uart_queue, &dest, portMAX_DELAY);
        xQueueReceive(uart_queue, &dato, portMAX_DELAY);
        if (dest == 'M' && dato == 'N') {
            LCD_command(0x01);
            delayMs(4);
            LCD_command(0x80);
            LCD_string("Sin paquete");
            LCD_command(0xC0);
            LCD_string("Elige otro FT");
            delayMs(2000);
            continue;
        } else if (dest == 'M' && dato == 'S') {
            LCD_command(0x01);
            delayMs(4);
            LCD_command(0x80);
            LCD_string("Esperando...");
            LCD_command(0xC0);
            LCD_string("Robot en camino");
            while (1) {
                xQueueReceive(uart_queue, &dest, portMAX_DELAY);
                xQueueReceive(uart_queue, &dato, portMAX_DELAY);
                if (dest == 'M' && dato == 'R') {
                    LCD_command(0x01);
                    delayMs(4);
                    LCD_command(0x80);
                    LCD_string("Toma tu paquete");
                    LCD_command(0xC0);
                    LCD_string("Presiona tecla");
                    get_key_pressed();
                    return;
                }
            }
        }
    }
}

void TPM0_init(void) {
    SIM->SCGC6 |= SIM_SCGC6_TPM0_MASK;
    SIM->SOPT2 |= SIM_SOPT2_TPMSRC(1);
    TPM0->SC  = 0; TPM0->CNT = 0;
    TPM0->MOD = 3000 - 1;
    TPM0->SC  = TPM_SC_CMOD(1) | TPM_SC_PS(4) | TPM_SC_TOF_MASK;
}

void delayMs(int n) {
    if (xTaskGetSchedulerState() != taskSCHEDULER_NOT_STARTED) {
        vTaskDelay(pdMS_TO_TICKS(n));
    } else {
        for (int i = 0; i < n; i++) {
            while ((TPM0->SC & 0x80) == 0) {}
            TPM0->SC |= 0x80;
        }
    }
}

void delayUs(int n) {
   (void)n;
    while((TPM0->SC & 0x80) == 0) {}
    TPM0->SC |= 0x80;
}

void UART1_init(uint32_t baud) {
    SIM->SCGC4 |= SIM_SCGC4_UART1_MASK;
    UART1->C2 = 0;
    uint16_t sbr = 24000000 / (16 * baud);
    UART1->BDH = (sbr >> 8) & 0x1F;
    UART1->BDL = sbr & 0xFF;
    UART1->C1  = 0;
    UART1->C2  = UART_C2_TE_MASK | UART_C2_RE_MASK;
}

void UART1_send_char(char c) {
    while (!(UART1->S1 & UART_S1_TDRE_MASK));
    UART1->D = c;
}

void keypad_init(void) {
    PTC->PDDR = 0x0F;
}

char keypad_getkey(void) {
    int row, col;
    const char row_select[] = {0x01, 0x02, 0x04, 0x08};
    taskENTER_CRITICAL();
    PTC->PDDR = 0x0F;
    PTC->PCOR = 0x0F;
    for(volatile int i = 0; i < 100; i++) {}
    col = PTC->PDIR & 0xF0;
    if (col == 0xF0) {
        PTC->PDDR = 0;
        taskEXIT_CRITICAL();
        return 0;
    }
    for (row = 0; row < 4; row++) {
        PTC->PDDR = row_select[row];
        PTC->PCOR = row_select[row];
        for(volatile int i = 0; i < 100; i++) {}
        col = PTC->PDIR & 0xF0;
        if (col != 0xF0) break;
        PTC->PDDR = 0;
    }
    PTC->PDDR = 0;
    taskEXIT_CRITICAL();
    if (row == 4) return 0;
    if (col == 0xE0) return row * 4 + 1;
    if (col == 0xD0) return row * 4 + 2;
    if (col == 0xB0) return row * 4 + 3;
    if (col == 0x70) return row * 4 + 4;
    return 0;
}

char get_key_pressed(void) {
    int code;
    while (keypad_getkey() != 0) {}
    delayMs(20);
    do {
    	code = keypad_getkey();
    }
    while (code == 0);
    delayMs(20);
    return keymap[code - 1];
}

void LCD_command(unsigned char command) {
    PTA->PCOR = RS | RW;
    PTD->PDOR = (PTD->PDOR & 0x0F) | ((command >> 4) << 4);
    PTA->PSOR = EN;
    delayMs(1);
    PTA->PCOR = EN;
    PTD->PDOR = (PTD->PDOR & 0x0F) | ((command & 0x0F) << 4);
    PTA->PSOR = EN;
    delayMs(1);
    PTA->PCOR = EN;
    delayMs(1);
    if (command < 4)
    	delayMs(4);
    else
    	delayMs(1);
}

void LCD_data(unsigned char data) {
    PTA->PSOR = RS;
    PTA->PCOR = RW;
    PTD->PDOR = (PTD->PDOR & 0x0F) | ((data >> 4) << 4);
    PTA->PSOR = EN;
    delayMs(1);
    PTA->PCOR = EN;
    PTD->PDOR = (PTD->PDOR & 0x0F) | ((data & 0x0F) << 4);
    PTA->PSOR = EN;
    delayMs(1);
    PTA->PCOR = EN;
    delayMs(1);
}

void LCD_string(char cadena[]) {
    int i = 0;
    while(cadena[i] != 0) {
    	LCD_data(cadena[i]);
    	i++;
    }
}

void LCD_init(void) {
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
    LCD_command(0x06);
    LCD_command(0x01);
    delayMs(4);
    LCD_command(0x0F);
}

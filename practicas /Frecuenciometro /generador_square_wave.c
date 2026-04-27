// GENERADOR DE SEÑAL CUADRADA
#include <MKL25Z4.H>
#include <stdint.h>

#define TIMER_CLOCK_HZ 32768UL


uint8_t TPM0_set_square_wave(uint8_t seconds);
void     delayMs(int n);
void     delayUs(int n);

int main(void) {
    // LED rojo (PTD1) para parpadeo al final
    SIM->SCGC5|= 0x1000;
    PORTD->PCR[1] = 0x100;
    PTD->PDDR |= 0x02;
    PTD->PSOR = 0x02;// apagado (activo-bajo)

	TPM0_set_square_wave(0.02); //50Hz
	while (1){
        int i;
        for (i = 0; i < 100; i++) {
            PTD->PTOR = 0x02; //toggle LED
            delayMs(20);
        }
	} //generamos la señal

}

uint8_t TPM0_set_square_wave(uint8_t seconds){
	if (seconds == 0 || seconds > 99) return 0;

	uint8_t ps_bits = 0x07; //prescaler /128
	uint32_t ps_div = 129;
	uint32_t mod = (TIMER_CLOCK_HZ*(uint32_t)seconds)/ ps_div - 1;

	//clocks de periféricos
	SIM->SCGC6 |= SIM_SCGC6_TPM0_MASK;     // Clock para TPM0
	SIM->SCGC5 |= SIM_SCGC5_PORTD_MASK;    // Clock para Puerto D
	SIM->SOPT2 |= SIM_SOPT2_TPMSRC(1);     // Fuente: MCGFLLCLK (o OSCERCLK)

	//Habilitamos el reloj interno lento
	MCG ->C1 |= MCG_C1_IRCLKEN_MASK;

	//pin PTD0 como TMPO_CH0
	TPM0->SC     = 0;
	TPM0->CNT    = 0;
	TPM0->MOD    = (uint16_t)mod;

	//set on reload, clear on match
	//config canal 0
	TPM0->CONTROLS[0].CnSC = TPM_CnSC_MSB_MASK | TPM_CnSC_ELSB_MASK;
	TPM0->CONTROLS[0].CnV  = (uint16_t)(mod / 2); // Duty cycle 50% = señal cuadrada
	//arrancamos el timer con un prescaler de 128 y CMOD = 01
	TPM0->SC     = ps_bits | TPM_SC_CMOD(1);
	return 1; }

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

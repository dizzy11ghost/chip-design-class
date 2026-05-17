/* Generate 60Hz PWM
 * TPM0 uses MCGFLLCLK which is 41.94 MHz.

 * The prescaler is set to divide by 16.

 * The modulo register is set to 43702 and the CnV */

#include <MKL25Z4.H>

void pwm_change(int numero);

int main(void) {
	SIM->SCGC5 |= 0x1000; /* enable clock to Port D */
	PORTD->PCR[1] = 0x0400; /* PTD1 used by TPM0 */
	SIM->SCGC6 |= 0x01000000; /* enable clock to TPM0 */
	SIM->SOPT2 |= 0x01000000; /* use MCGFLLCLK as timer counter clock */

	TPM0->SC = 0; /* disable timer */
	/* edge-aligned, pulse high */
	TPM0->CONTROLS[1].CnSC = 0x20 | 0x08;
	/* Set up modulo register for 60 kHz */
	TPM0->MOD = 43702;
	TPM0->SC = 0x0C; /* enable TPM0 with prescaler /16 */
	while (1) {
	}
}

/* Funcion de actualizar PWM con valor (de 0 a 4)
 *
 * Para usar el cambio tienes que usar esta linea "pwm_change(numero int de la opcion de 0-4);"
 */

void pwm_change(int numero) {
    switch(numero) {
        case 0:
            TPM0->CONTROLS[1].CnV = 0;      /* 0% Duty Cycle */
            break;
        case 1:
            TPM0->CONTROLS[1].CnV = 10925;  /* 25% Duty Cycle */
            break;
        case 2:
            TPM0->CONTROLS[1].CnV = 21851;  /* 50% Duty Cycle */
            break;
        case 3:
            TPM0->CONTROLS[1].CnV = 32777;  /* 75% Duty Cycle */
            break;
        case 4:
            TPM0->CONTROLS[1].CnV = 43703;  /* 100% Duty Cycle */
            break;
        default:
            /* Si llega un número diferente se apaga */
            TPM0->CONTROLS[1].CnV = 0;
            break;
    }
}

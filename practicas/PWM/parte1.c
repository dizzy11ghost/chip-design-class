/* Generate 60Hz PWM
 * TPM0 uses MCGFLLCLK which is 41.94 MHz.

 * The prescaler is set to divide by 16.

 * The modulo register is set to 43702 and the CnV */

#include <MKL25Z4.H>

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
	TPM0->CONTROLS[1].CnV = 0; // Modificar los valores en esta linea
	/* * Valores calculados (MOD = 43702):
	     * 0%   -> CnV = 0
	     * 25%  -> CnV = 10925
	     * 50%  -> CnV = 21851
	     * 75%  -> CnV = 32777
	     * 100% -> CnV = 43703
	     */
	TPM0->SC = 0x0C; /* enable TPM0 with prescaler /16 */
	while (1) {
	}
}

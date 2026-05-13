// Mini challenge 6 Frecuenciómetro
#include <MKL25Z4.H>

#define RS 0x04 /* PTA2 */
#define RW 0x10 /* PTA4 */
#define EN 0x20 /* PTA5 */
#define TIMER_CLOCK_HZ 20971520

uint8_t TPM0_set_period_seconds(uint8_t seconds);
void TPM1_input_capture_init(void);
void delayMs(int n);
void LCD_init(void);
void LCD_command(unsigned char command);
void LCD_data(unsigned char data);
void LCD_string(char cadena[]);

volatile uint32_t flank_count = 0;
volatile uint32_t frecuencia  = 0;
volatile uint8_t  flag_update = 0;

int main(void)
{
	LCD_init();
	SIM->SCGC5 |= 0x0400;
	PORTB->PCR[18] = 0x100;
	PTB->PDDR |= (1 << 18);
	PTB->PSOR  = (1 << 18);
	PORTB->PCR[19] = 0x100;
	PTB->PDDR |= (1 << 19);
	PTB->PSOR  = (1 << 19);
	LCD_command(0x80);
	LCD_string("Frecuencia:");
	delayMs(100);
	TPM1_input_capture_init();
	TPM0_set_period_seconds(1);
	TPM0->SC |= 0x40;
	NVIC_EnableIRQ(TPM0_IRQn);
	char buf[6];
	while (1)
	{
		if (flag_update)
	    {
			flag_update = 0;
	        LCD_command(0xC0);
	        LCD_string("    ");
	        LCD_command(0xC0);
	        buf[0] = '0' + (frecuencia / 1000);
	        buf[1] = '0' + ((frecuencia / 100) % 10);
	        buf[2] = '0' + ((frecuencia / 10) % 10);
	        buf[3] = '0' + (frecuencia % 10);
	        buf[4] = '\0';
	        LCD_string(buf);
	     }
	  }
}

void TPM1_IRQHandler(void)
{
    volatile uint32_t dummy;
    if (TPM1->CONTROLS[0].CnSC & 0x80)
    {
        flank_count++;
        PTB->PTOR = (1 << 19);
        dummy = TPM1->CONTROLS[0].CnV;
        TPM1->CONTROLS[0].CnSC |= 0x80;
    }
}

void TPM0_IRQHandler(void)
{
    frecuencia  = flank_count;
    flank_count = 0;
    PTB->PTOR = (1 << 18);
    flag_update = 1;
    TPM0->SC |= 0x80;
}

void TPM1_input_capture_init(void)
{
    SIM->SCGC5 |= 0x0200;
    SIM->SCGC6 |= 0x02000000;
    SIM->SOPT2 = (SIM->SOPT2 & ~0x03000000) | 0x03000000;
    PORTA->PCR[12] = 0x300;
    TPM1->SC  = 0;
    TPM1->CNT = 0;
    TPM1->MOD = 0xFFFF;
    TPM1->CONTROLS[0].CnSC = 0x44;
    NVIC_EnableIRQ(TPM1_IRQn);
    TPM1->SC = 0x08;
}

#define TIMER_CLOCK_HZ 20971520

uint8_t TPM0_set_period_seconds(uint8_t seconds)
{
    if (seconds == 0 || seconds > 99)
        return 0;
    SIM->SCGC6 |= 0x01000000;
    SIM->SOPT2 |= 0x01000000;
    SIM->SOPT2 = (SIM->SOPT2 & ~0x03000000) | 0x03000000; // TPMSRC = MCGIRCLK
    MCG->C2 |= MCG_C2_IRCS_MASK;
    MCG->C1 |= MCG_C1_IRCLKEN_MASK;
    uint32_t timer_clk = 2000000;
    uint8_t  ps_bits   = 0x07; // /128
    uint32_t ps_div    = 128;
    uint32_t mod = (timer_clk * (uint32_t)seconds) / ps_div - 1;
    TPM0->SC  = 0;
    TPM0->CNT = 0;
    TPM0->MOD = (uint16_t)mod;
    TPM0->SC  = ps_bits;
    TPM0->SC |= 0x08;
    return 1;
}

void LCD_init(void)
{
    SIM->SCGC5 |= 0x1000;
    PORTD->PCR[4] = 0x100;
    PORTD->PCR[5] = 0x100;
    PORTD->PCR[6] = 0x100;
    PORTD->PCR[7] = 0x100;
    PTD->PDDR = 0xFF;
    SIM->SCGC5 |= 0x0200;
    PORTA->PCR[2] = 0x100;
    PORTA->PCR[4] = 0x100;
    PORTA->PCR[5] = 0x100;
    PTA->PDDR |= 0x34;
    PTA->PCOR  = RS | RW;
    delayMs(100);
    PTD->PDOR = (0x03 << 4);
    PTA->PSOR = EN;
    delayMs(1);
    PTA->PCOR = EN;
    delayMs(20);
    PTD->PDOR = (0x03 << 4);
    PTA->PSOR = EN;
    delayMs(1);
    PTA->PCOR = EN;
    delayMs(5);
    PTD->PDOR = (0x03 << 4);
    PTA->PSOR = EN;
    delayMs(1);
    PTA->PCOR = EN;
    delayMs(5);
    PTD->PDOR = (0x02 << 4);
    PTA->PSOR = EN;
    delayMs(1);
    PTA->PCOR = EN;
    delayMs(5);
    LCD_command(0x28);
    LCD_command(0x06);
    LCD_command(0x01);
    delayMs(4);
    LCD_command(0x0C);
}

void LCD_command(unsigned char command)
{
    PTA->PCOR = RS | RW;
    PTD->PDOR =
        (PTD->PDOR & 0x0F) | ((command >> 4) << 4);
    PTA->PSOR = EN;
    delayMs(1);
    PTA->PCOR = EN;
    PTD->PDOR =
        (PTD->PDOR & 0x0F) | ((command & 0x0F) << 4);
    PTA->PSOR = EN;
    delayMs(1);
    PTA->PCOR = EN;
    if (command < 4)
        delayMs(4);
    else
        delayMs(1);
}

void LCD_data(unsigned char data)
{
    PTA->PSOR = RS;
    PTA->PCOR = RW;
    PTD->PDOR =
        (PTD->PDOR & 0x0F) | ((data >> 4) << 4);
    PTA->PSOR = EN;
    delayMs(1);
    PTA->PCOR = EN;
    PTD->PDOR =
        (PTD->PDOR & 0x0F) | ((data & 0x0F) << 4);
    PTA->PSOR = EN;
    delayMs(1);
    PTA->PCOR = EN;
    delayMs(1);
}

void LCD_string(char cadena[])
{
    int i = 0;
    while (cadena[i] != 0)
    {
        LCD_data(cadena[i]);
        i++;
    }
}

void delayMs(int n)
{
    int i, j;
    for (i = 0; i < n; i++)
    {
        for (j = 0; j < 7000; j++)
        {
            __asm("nop");
        }
    }
}

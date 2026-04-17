#include <MKL25Z4.H>
#include <stdio.h>

//UART
void UART0_Init(void) {
    SIM->SCGC6 |= SIM_SCGC4_UART0_MASK; // Enable clock for UART0
    SIM->SOPT2 |= SIM_SCGC5_PORTD_MASK; // Enable clock for PORTD

    //PTD2 RX y PTD3 Tx
    PORTD->PCR[2] = PORT_PCR_MUX(3);
    PORTD->PCR[3] = PORT_PCR_MUX(3);

    SIM->SOPT2 |= 0x01000000; //48 Hz

    //baud rate 115200
    uint16_t sbr = 26; //uint16_t es un tipo de dato sin signo de 16 bits, sbr significa "Serial Baud Rate" (tasa de baudios serial), se utiliza para calcular la velocidad de transmisión de datos en la comunicación UART. El valor de sbr se calcula utilizando la fórmula: sbr = (frecuencia del reloj) / (16 * baud rate)
    UART0 -> BDH = (sbr >> 8) & UART_BDH_SBR_MASK;
    UART0 -> BDL = (sbr & UART_BDL_SBR_MASK);

    UART0 -> C4 = 15; //OSR - OverSampling Ratio: define cuántas veces muestrea RX cada bit recibido para asegurar una lectura correcta
    UART0 -> C2 |= UART_C2_TE_MASK | UART_C2_RE_MASK; //Or para decir que se van a usar ambos bits, TE para Transmit Enable (habilitar transmisión) y RE para Receive Enable (habilitar recepción)
}

//Para mandar un byte
void UART0_SendByte(uint8_t data) {
    while (!(UART0->S1 & UART_S1_TDRE_MASK)); // Espera hasta que el buffer de transmisión esté vacío
    UART0->D = data; // Envía el byte
}

//Para mandar un Buffer
void UART0_SendBuffer(uint8_t*data, uint8_t length) {
    for (int i = 0; i < length; i++) {
        UART0_SendByte(data[i]); // Envía cada byte del buffer
    }
}

//Para Checksum
//(Checksum lo que hace es que verifica la integridad de los datos transmitidos, sumando todos los bytes del mensaje y tomando el complemento a uno del resultado. El receptor puede realizar la misma operación y comparar el resultado con el checksum recibido para asegurarse de que los datos no se han corrompido durante la transmisión.)
uint8_t checksum(uint8_t*data, uint8_t lenght) {
    uint8_t sum = 0; //inicializamos la variable
    //vamos a usar un for para recorrer el buffer de datos, sumando cada byte al total
    for (int i = 0; i < lenght; i++) {
        sum += data[i]; //sumamos cada byte al total
    }
    return ~sum; //retornamos el complemento a uno del resultado
}

//TEST PARA MOVIMIENTO AAAA
void Dobot_testmove(){
    //Ojo!! esto es una prube inicial
    uint8_t cmd[32]; //el cmd es el comando que se va a enviar al Dobot, es un arreglo de bytes que contiene la información del movimiento que queremos realizar
    int i = 0;

    //header
    cmd[i++] = 0xAA; //header del mensaje, es un byte que indica el inicio de un mensaje
    cmd[i++] = 0xAA; //header del mensaje, es un byte que indica el inicio de un mensaje

    //lenght
    cmd[i++] = 0x0F;

    //id: identificador único, para identificación segura
    //ptp command: precision time protocol, configura dispositivos para sincronizar sus relojs con más precisión
    cmd[i++] = 0x54; //se usa 54 porque es el comando para movimiento PTP (Precision Time Protocol) en el Dobot, que permite controlar el movimiento del brazo robótico con precisión.

    //control
    cmd[i++] = 0x03; //write + queued

    //Parámetros del movimiento
    //(coordenadas en x, y, z, y r)
    float x = 200.0f; //coordenada x a la que queremos mover el brazo robótico, se define como un número de punto flotante (float) para permitir valores decimales
    float y = 0.0f;
    float z = 50.0f;
    float r = 0.0f;

    uint8_t *px = (uint8_t*)&x;
    uint8_t *py = (uint8_t*)&y;
    uint8_t *pz = (uint8_t*)&z;
    uint8_t *pr = (uint8_t*)&r;

    //vamos a usar for para copiar los bytes de cada coordenada al cmd, usando un puntero para acceder a cada byte de la variable float
    for(int j=0; j<4; j++) cmd[i++] = px[j];
    for(int j=0; j<4; j++) cmd[i++] = py[j];
    for(int j=0; j<4; j++) cmd[i++] = pz[j];
    for(int j=0; j<4; j++) cmd[i++] = pr[j];

    //checksum para validar los datos
    cmd[i++] = checksum(cmd, i);

    UART0_SendBuffer(cmd, i);
}

// main main main main main wuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuu
int main(void){
    UART0_Init();

    //delay simple
    for (volatile int i=0; i< 1000000; i++);

    //intento de movimiento (recemos)
    Dobot_testmove();

    while (1){

    }
}

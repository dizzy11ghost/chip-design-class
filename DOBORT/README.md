Notes to self!!
Acerca del brazo: 
*El Dobot espera un frame binario, típicamente:
    [Header][Length][ID][Ctrl][Params][Checksum]

*1. Conexión física (rápido pero crítico)

  En la FRDM-KL25Z:
  PTD2 → UART0_RX
  PTD3 → UART0_TX
  
  Conecta:
  TX (KL25Z) → RX (Dobot)
  RX (KL25Z) → TX (Dobot)
  GND ↔ GND
  
  Baudrate:
  115200, 8N1

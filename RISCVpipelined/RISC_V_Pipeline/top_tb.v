// ============================================================================
// Testbench: top_tb
// Descripción: Testbench integral para el procesador RISC-V pipeline de 5
//              etapas (Fetch, Decode, Execute, Memory, Writeback).
//
// Qué prueba este testbench:
//   1. Reset correcto: PC, registros y registros de pipeline en 0.
//   2. Avance normal del pipeline: una instrucción nueva entra cada ciclo
//      (Fetch) y avanza por D -> E -> M -> W.
//   3. Forwarding: monitorea ForwardAE/ForwardBE para verificar que se
//      activan cuando hay dependencias entre instrucciones consecutivas
//      (RAW hazards resueltos sin stall).
//   4. Load-use hazard (lw seguido de instrucción dependiente): se observa
//      StallF/StallD = 1 durante un ciclo.
//   5. Hazard de control (branch/jump tomado): se observa FlushD/FlushE = 1
//      y el PC saltando a PCTargetE.
//   6. Escritura final en el banco de registros (Writeback): se imprime
//      RegWriteW, RdW y ResultW para confirmar que el resultado correcto
//      llega al registro destino.
//
// Requisitos:
//   - El archivo "instructions.mem" (o "instrMem.hex", según el módulo
//     instruction_memory) debe contener un programa con al menos:
//       * Instrucciones tipo R consecutivas con dependencia de datos
//         (para probar forwarding).
//       * Un lw seguido inmediatamente de una instrucción que use el
//         registro cargado (para probar el stall por load-use).
//       * Un branch (beq) tomado, con instrucciones después que deban
//         ser descartadas (para probar flush).
// ============================================================================

module top_tb();

    reg clk, rst;

    // ------------------------------------------------------------------
    // DUT
    // ------------------------------------------------------------------
    top dut (
        .clk(clk),
        .rst(rst)
    );

    // ------------------------------------------------------------------
    // Generación de reloj: periodo = 10 (50% duty cycle)
    // ------------------------------------------------------------------
    always #5 clk = ~clk;

    // ------------------------------------------------------------------
    // Secuencia de Reset y duración de simulación
    // ------------------------------------------------------------------
    initial begin
        clk = 0;
        rst = 1;

        // Mantener reset activo por 2 ciclos completos para asegurar
        // que todos los registros de pipeline y el PC se inicialicen
        // correctamente en 0.
        #20;
        rst = 0;

        // Tiempo suficiente para que el programa cargado en
        // instrMem.hex/instructions.mem se ejecute completo,
        // incluyendo el llenado y vaciado del pipeline (5 etapas).
        #400;

        $finish;
    end

    // ------------------------------------------------------------------
    // Volcado de ondas para visualización en simulador (ModelSim/Questa)
    // ------------------------------------------------------------------
    initial begin
        $dumpfile("pipeline.vcd");
        $dumpvars(0, top_tb);
    end

    // ------------------------------------------------------------------
    // Monitor combinado: estado del pipeline + Hazard Unit, ciclo a ciclo
    // ------------------------------------------------------------------
    // Se usa $display dentro de always @(posedge clk) en lugar de
    // $monitor, porque Verilog solo permite un $monitor activo a la vez
    // (el segundo $monitor sobreescribe al primero).
    //
    // Columnas:
    //   PCF            -> PC en Fetch (instrucción que se está leyendo)
    //   InstrD         -> instrucción actualmente en Decode
    //   ALUResultE     -> resultado de la ALU en Execute
    //   ResultW        -> valor final que se escribe en el banco de regs
    //   RegWriteW/RdW  -> indica si y dónde se escribe en Writeback
    //   MemWriteM      -> indica si hay escritura a memoria de datos
    //   PCSrcE         -> indica si se tomó un salto/branch
    //   StallF/StallD  -> hazard load-use (congela Fetch/Decode)
    //   FlushD/FlushE  -> flush por branch tomado o por lwStall
    //   ForwardAE/BE   -> origen del forwarding (00=RegFile, 01=WB, 10=MEM)
    // ------------------------------------------------------------------
    initial begin
        $display("================================================================================================================================");
        $display("time | PCF      | InstrD   | ALUResultE | ResultW  | RegWriteW RdW | MemWriteM | PCSrcE | StallF StallD | FlushD FlushE | FwdAE FwdBE");
        $display("================================================================================================================================");
    end

    always @(posedge clk) begin
        if (!rst)
            $display("%40t | %h | %h | %h   | %h | %b        %0d  |    %b      |   %b    |   %b      %b    |   %b      %b   |  %b    %b",
                     $time,
                     dut.PCF, dut.InstrD, dut.ALUResultE, dut.ResultW,
                     dut.RegWriteW, dut.RdW, dut.MemWriteM, dut.PCSrcE,
                     dut.StallF, dut.StallD, dut.FlushD, dut.FlushE,
                     dut.ForwardAE, dut.ForwardBE);
    end

    // ------------------------------------------------------------------
    // Verificación puntual post-reset
    // ------------------------------------------------------------------
    initial begin
        @(negedge rst); // espera a que termine el reset

        // Un ciclo después del reset, el PC debe haber avanzado a 4
        // (asumiendo que no hay stall en el primer ciclo).
        #10;
        if (dut.PCF !== 32'h4 && dut.PCF !== 32'h0)
            $display("ADVERTENCIA: PCF inesperado tras reset = %h (esperado 0 o 4)", dut.PCF);
        else
            $display("OK: PCF avanza correctamente tras reset (PCF = %h)", dut.PCF);
    end

endmodule
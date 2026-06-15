module top_tb();
    reg clk, rst;
    
    top dut (
        .clk(clk),
        .rst(rst)
    );

    always #5 clk = ~clk; //generación de reloj

    initial begin
        clk = 0;
        rst = 1;

        #20; //esperamos para que el sistema se estabilice
        rst = 0;
        
        #400; //tiempo para las 5 etapas

        $finish;
    end

    initial begin
        $dumpfile("pipeline.vcd");
        $dumpvars(0, top_tb);
    end

    initial begin //display para visualizar resultados
        $display("time | PCF      | InstrD   | ALUResultE | ResultW  | RegWriteW RdW | MemWriteM | PCSrcE | StallF StallD | FlushD FlushE | FwdAE FwdBE");
    end

    always @(posedge clk) begin
        if (!rst)
            $display("%40t | %h | %h | %h   | %h | %b        %0d  |    %b      |   %b    |   %b      %b    |   %b      %b   |  %b    %b",
                     $time, dut.PCF, dut.InstrD, dut.ALUResultE, dut.ResultW, dut.RegWriteW, dut.RdW, dut.MemWriteM, dut.PCSrcE, dut.StallF, dut.StallD, dut.FlushD, dut.FlushE, dut.ForwardAE, dut.ForwardBE);
    end

    initial begin
        @(negedge rst); //cuando acabe el rst

        //para checar PC+4
        #10;
        if (dut.PCF !== 32'h4 && dut.PCF !== 32'h0)
            $display("ADVERTENCIA: PC inesperado tras reset = %h (esperado 0 o 4)", dut.PCF);
        else
            $display("OK: PC avanza correctamente tras reset (PC = %h)", dut.PCF);
    end

endmodule

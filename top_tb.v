`timescale 1ns/1ps

module top_tb();
    reg clk;
    reg reset;

    top DUT(.clk(clk), .reset(reset));

    always #10 clk = ~clk; //20 ns
    initial begin
        clk = 0;
        reset = 1;
        #10;
        reset = 0;
        #100;
        $finish;
    end

    initial begin
        $monitor(
        "t=%0d | PC=%h | Instr=%h | SrcA=%h | SrcB=%h | imm=%h | ALUCtrl=%b | ALU_result=%h",
            $time,
            DUT.PC,
            DUT.Instr,
            DUT.SrcA,
            DUT.SrcB,
            DUT.immExt,
            DUT.alu_control,
            DUT.alu_result
        );

    end

    initial begin
        $dumpfile("top_tb.vcd");
        $dumpvars(0, top_tb);  
    end

endmodule
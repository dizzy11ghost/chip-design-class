module instruction_memory( //?
	input clk,
	input [31:0] A, //address Input
	output reg [31:0] RD //instruction output
);
	//Friendly reminder: modificar datos leídos de la ROM
	reg [31:0] instr_mem [0:2];
	
	initial begin
		$readmemh("instrMem.hex", instr_mem);
	end
	
	//leemos la operación
	always @(*) begin
		if (A[4:2] <= 2)
        	RD = instr_mem[A[4:2]];
		else
			RD = 32'b0;
	end

endmodule
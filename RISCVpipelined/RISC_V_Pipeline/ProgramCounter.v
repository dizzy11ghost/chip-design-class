module ProgramCounter(
	input clk,
	input rst,
	input EN,
	input [31:0] PCNext,
	output reg [31:0] PC
);

	always @(posedge clk) begin
		if (rst)
			PC <= 32'b0;
		else if (EN)
			PC <= PCNext;
	end

endmodule
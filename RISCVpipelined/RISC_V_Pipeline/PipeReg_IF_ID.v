module PipeReg_IF_ID(
	input clk,
	input rst,
	input EN,
	input CLR,
	input [31:0] InstrF,
	input [31:0] PCF,
	input [31:0] PCPlus4F,
	output reg [31:0] InstrD,
	output reg [31:0] PCD,
	output reg [31:0] PCPlus4D
);

	always @(posedge clk) begin
		if (rst || CLR) begin
			InstrD <= 32'b0;
			PCD <= 32'b0;
			PCPlus4D <= 32'b0;
		end
		else if (EN) begin
			InstrD <= InstrF;
			PCD <= PCF;
			PCPlus4D <= PCPlus4F;
		end
	end

endmodule
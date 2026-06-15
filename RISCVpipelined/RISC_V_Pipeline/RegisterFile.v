module RegisterFile(
	input clk,
	input rst,
	input WE3,
	input [4:0] A1, A2, A3,
	input [31:0] WD3,
	output reg [31:0] RD1, RD2
);

	reg [31:0] registros [31:0];
	integer i;

	always @(*) begin
		RD1 = (A1 == 5'b0) ? 32'b0 : registros[A1];
		RD2 = (A2 == 5'b0) ? 32'b0 : registros[A2];
	end

	always @(posedge clk) begin
		if (rst) begin
			for (i = 0; i < 32; i = i + 1)
				registros[i] <= 32'b0;
		end
		else if (WE3 && (A3 != 5'b0)) begin
			registros[A3] <= WD3;
		end
	end

endmodule
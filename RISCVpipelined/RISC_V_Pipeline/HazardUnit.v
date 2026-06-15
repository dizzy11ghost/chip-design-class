module HazardUnit(
	input [4:0] Rs1D,
	input [4:0] Rs2D,
	input [4:0] Rs1E,
	input [4:0] Rs2E,
	input [4:0] RdE,
	input [4:0] RdM,
	input [4:0] RdW,
	input RegWriteM,
	input RegWriteW,
	input ResultSrcE0, 
	input PCSrcE,      
	output StallF,
	output StallD,
	output FlushD,
	output FlushE,
	output [1:0] ForwardAE,
	output [1:0] ForwardBE
);

	assign ForwardAE =
		((Rs1E == RdM) && RegWriteM && (Rs1E != 5'b0)) ? 2'b10 :
		((Rs1E == RdW) && RegWriteW && (Rs1E != 5'b0)) ? 2'b01 :
		2'b00;

	assign ForwardBE =
		((Rs2E == RdM) && RegWriteM && (Rs2E != 5'b0)) ? 2'b10 :
		((Rs2E == RdW) && RegWriteW && (Rs2E != 5'b0)) ? 2'b01 :
		2'b00;

	wire lwStall;
	assign lwStall = ((Rs1D == RdE) || (Rs2D == RdE)) && ResultSrcE0;

	assign StallF = lwStall;
	assign StallD = lwStall;
	
	assign FlushD = PCSrcE;
	assign FlushE = lwStall || PCSrcE;

endmodule
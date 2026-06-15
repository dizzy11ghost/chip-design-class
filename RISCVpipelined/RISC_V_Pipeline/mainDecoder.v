module mainDecoder(
	input [6:0] opcode, 
	output reg RegWrite,
	output reg [1:0] ImmSrc,
	output reg ALUSrc,
	output reg MemWrite,
	output reg [1:0] ResultSrc,
	output reg Branch,
	output reg [1:0] ALUOp,
	output reg Jump	
);

	localparam Ltype = 3, Stype = 35, Rtype = 51, Btype = 99, Itype = 19, Jtype = 111;
	
	always @(*) begin
		casex(opcode)
			Ltype: begin
						RegWrite = 1;
						ImmSrc = 2'b00;
						ALUSrc = 1;
						MemWrite = 0;
						ResultSrc = 2'b01;
						Branch = 0;
						ALUOp = 2'b00;
						Jump = 0;
					end
			Stype: begin
						RegWrite = 0;
						ImmSrc = 2'b01;
						ALUSrc = 1;
						MemWrite = 1;
						ResultSrc = 2'bxx;
						Branch = 0;
						ALUOp = 2'b00;
						Jump = 0;
					end
			Rtype: begin
						RegWrite = 1;
						ImmSrc = 2'bxx;
						ALUSrc = 0;
						MemWrite = 0;
						ResultSrc = 2'b00;
						Branch = 0;
						ALUOp = 2'b10;
						Jump = 0;
					end
			Btype: begin
						RegWrite = 0;
						ImmSrc = 2'b10;
						ALUSrc = 0;
						MemWrite = 0;
						ResultSrc = 2'bxx;
						Branch = 1;
						ALUOp = 2'b01;
						Jump = 0;
					end
			Itype: begin
						RegWrite = 1;
						ImmSrc = 2'b00;
						ALUSrc = 1;
						MemWrite = 0;
						ResultSrc = 2'b00;
						Branch = 0;
						ALUOp = 2'b10;
						Jump = 0;
					end
			Jtype: begin
						RegWrite = 1;
						ImmSrc = 2'b11;
						ALUSrc = 1'bx;
						MemWrite = 0;
						ResultSrc = 2'b10;
						Branch = 0;
						ALUOp = 2'bxx;
						Jump = 1;
					end
			default: begin
						RegWrite = 0;
						ImmSrc = 2'b00;
						ALUSrc = 0;
						MemWrite = 0;
						ResultSrc = 2'b00;
						Branch = 0;
						ALUOp = 2'b00;
						Jump = 0;
					end
			endcase
		end
endmodule
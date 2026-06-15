module ALUdecoder(
	input [1:0] ALUOp,
	input op,
	input [2:0] funct3,
	input funct7,
	output reg [2:0] Control
);
	
	always @(*) begin
		case(ALUOp)
			2'b00: Control = 0;
			2'b01: Control = 1;
			2'b10: begin
				casex({funct3, op, funct7})
					5'b00000: Control = 0;
					5'b00001: Control = 0;
					5'b00010: Control = 0;
					5'b00011: Control = 1;
					5'b010xx: Control = 3'b101;
					5'b110xx: Control = 3'b011;
					5'b111xx: Control = 3'b010;
				endcase
			end
		endcase
	end
	
endmodule
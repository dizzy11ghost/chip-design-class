module ALUdecoder(
	input op,
	input [2:0] funct3, //funct3 de la instrucción: sirve para distinguir entre instrucciones tipo R, I, S, B
	input funct7, 
	input [1:0] ALUop,
	output reg [2:0] control //señal de control
);
	
	always @(*) begin
		case(ALUop)
			2'b00: begin
				control = 3'b000; //add
			end
			2'b01: begin 
			    control = 3'b001; //sub 
			end
			2'b10: begin
				casex({funct3, funct7, op})
					5'b00000: control = 3'b000;
					5'b00001: control = 3'b000;
					5'b00010: control = 3'b010;
					5'b00011: control = 3'b001;
					5'b010xx: control = 3'b101;
					5'b110xx: control = 3'b011;
					5'b111xx: control = 3'b010;
					default: control = 3'b000;
					
				endcase
			end
			default: control = 3'b000;
		endcase
	end
	
endmodule

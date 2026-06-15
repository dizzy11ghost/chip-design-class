module ALU(
	input[31:0] A, 
	input[31:0] B,
	input [2:0] Control,
	output reg [31:0] Result,
	output reg Zero
);
	
	localparam add = 3'b000, sub = 3'b001, andd = 3'b010, orr = 3'b011, slt = 3'b101;

	always @(*) begin
		case(Control)
			add: Result = A + B;
			sub: Result = A - B;
			andd: Result = A & B;
			orr: Result = A | B;
			slt: Result = A << B;
			default: Result = 0;
		endcase
		if(Result == 0)
			Zero = 1;
		else
			Zero = 0;
	end
	
endmodule
		
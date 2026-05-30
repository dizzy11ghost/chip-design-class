module extend(
    input [31:0] instruction,
    input [1:0] ImmSrc,
    output reg [31:0] imm_out
);

always@(*) begin
    case(ImmSrc)
        2'b00: begin
            imm_out = {{20{instruction[31]}}, instruction[31:20]}; //I-type
        end
        2'b01: begin
            imm_out = {{20{instruction[31]}}, instruction[31:25], instruction[11:7]}; //S-type
        end
        2'b10: begin
            imm_out = {{20{instruction[31]}}, instruction[31], instruction[7], instruction[30:25], instruction[11:8], 1'b0}; //B-type
        end
        2'b11: begin
            imm_out = {{12{instruction[31]}}, instruction[19:12], instruction[20], instruction[30:21], 1'b0}; //J-type
        end
        default: begin
            imm_out = 32'b0; //valor indefinido
        end
    endcase
end
endmodule

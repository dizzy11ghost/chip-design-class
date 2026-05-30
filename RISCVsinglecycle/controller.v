module controller(
    input wire [6:0] op,
    input wire [2:0] funct3,
    input wire funct7b5,
    input wire zero,
    output wire [1:0] resultSrc,
    output wire MemWrite, PCSrc, ALUSrc, RegWrite, 
    output wire [1:0] ImmSrc,
    output wire [2:0] control
);
wire [1:0] ALUOp;
wire jump;
wire branch;
//instanciamos main decoder que interpretará el opcope
main_decoder md(
    .op(op), 
    .ResultSrc(resultSrc), 
    .MemWrite(MemWrite), 
    .Branch(branch), 
    .ALUSrc(ALUSrc), 
    .ALUOp(ALUOp), 
    .RegWrite(RegWrite), 
    .ImmSrc(ImmSrc), 
    .Jump(jump)
);
ALUdecoder ad (
    .op(op[5]),
    .funct3(funct3), 
    .funct7(funct7b5), 
    .ALUop(ALUOp), 
    .control(control)
);
assign PCSrc = branch & zero | jump;
endmodule

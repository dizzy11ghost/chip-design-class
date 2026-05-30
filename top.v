module top(
	input clk,
	input reset
	//como sólo dependemos del opcode, sólo necesitamos el clk y el reste
);
wire ALUSrc; //para ver si vamos a usar el i o un registro 
wire zero;//zero flag para las branches
wire MW;
wire branch;
wire RW; 
wire jump;
wire [1:0] resultSrc; //para ver si el resultado viene de la alu, de memoria o del program counter
wire PCSrc; //ramas y jumps
wire [31:0] PCTarget; 
wire [31:0] PCPlus4;
wire [31:0] Instr; //instrucción actual
wire [31:0] result; //resultado final que vamo a guardar en los registros
wire [31:0] RD2; //read data 2 si no usamos i
wire [31:0] immExt; //inmediato extendido
wire [31:0] SrcA; //operando A alu 
wire [31:0] SrcB; //operando B alu
wire [31:0] readData; //dato de la memoria que vamo a leer
wire [31:0] alu_result; 
wire [2:0] alu_control;
wire [31:0] PCNext; //friendly reminder: PCNext puede ser modificado por el +4 o por jumps y branches
wire [3:0] ALUFlags;
wire [1:0] immSrc; //Para ver qué show con el inmediato
reg  [31:0] PC; //program counter

always @(posedge clk or posedge reset) begin
	if (reset) begin
		PC <= 32'b0; 
	end else begin
		PC <= PCNext; //pasamos al siguiente valor de program counter
	end
end

multiplexor #(2) mux_B ( //multiplexor para SourceB de la ALU
    .mux_in({immExt, RD2}),
    .mux_sel(ALUSrc),
    .mux_out(SrcB)
);

adder addTarget( //
    .a(PC),
    .b(immExt),
    .y(PCTarget)
);

adder add4(
    .a(PC),
    .b(32'd4),
    .y(PCPlus4)
);

multiplexor #(2) mux_PC ( //multiplexor para el program counter
    .mux_in({PCTarget, PCPlus4}),
    .mux_sel(PCSrc),
    .mux_out(PCNext)
);

multiplexor #(3) mux_res(
    .mux_in({PCPlus4, readData, alu_result}),
    .mux_sel(resultSrc),
    .mux_out(result)
);

//modulos instanciados :D
instruction_memory instruc(
	.clk(clk),
	.A(PC), // dirección del PC para leer la instrucción
	.RD(Instr) //salida de la instrucción
);

reg_file rf(
	.clk(clk),
	.WE3(RW), //write enable
	.A1(Instr[19:15]), // registro 1
	.A2(Instr[24:20]), // registro 2
	.A3(Instr[11:7]),  // registro destino
	.WD3(result),// write data
	.RD1(SrcA), //read data reg 1
	.RD2(RD2) //reg 2
);

extend ex(
	.instruction(Instr), //instrucción para extraer i
	.ImmSrc(immSrc), 
	.imm_out(immExt) //i
);

alu_risc alu(
	.A(SrcA), 
	.B(SrcB), 
	.ALUControl(alu_control),
	.ALUResult(alu_result),
	.zero(zero)             
);

data_memory datamem(
	.clk(clk),
	.rst(reset),             
	.WE(MW),//write enable
	.A(alu_result),
	.WD(RD2), //write data
	.RD(readData) //read data
);

controller con(
	.op(Instr[6:0]), //opcode
	.funct3(Instr[14:12]),
	.funct7b5(Instr[30]), // bit 30 del campo funct7
	.zero(zero),
	.PCSrc(PCSrc),              
	.resultSrc(resultSrc),      
	.MemWrite(MW),
	.control(alu_control), 
	.ALUSrc(ALUSrc),  
	.ImmSrc(immSrc), 
	.RegWrite(RW) //Register Write
);

endmodule
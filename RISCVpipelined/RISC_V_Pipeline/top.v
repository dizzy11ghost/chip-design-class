// Módulo: top
// Descripción: Datapath RISC-V pipeline de 5 etapas (Fetch, Decode, Execute,
// Memory, Writeback) con unidad de hazards (forwarding, stall, flush).
// Conexiones siguiendo la nomenclatura de la presentación (sufijos F/D/E/M/W).
module top(
	input clk,
	input rst
);

	// ------------------------------------------------------------------
	// FETCH
	// ------------------------------------------------------------------
	wire [31:0] PCF, PCNext, PCPlus4F, InstrF;
	wire [31:0] PCTargetE;
	wire PCSrcE;
	wire StallF;

	multiplexor #(.N(2)) mux_pc (
		.mux_in  ({PCTargetE, PCPlus4F}),
		.mux_sel (PCSrcE),
		.mux_out (PCNext)
	);

	ProgramCounter mPC (
		.clk(clk),
		.rst(rst),
		.EN(~StallF),
		.PCNext(PCNext),
		.PC(PCF)
	);

	instruction_memory mInstrMem (
		.A(PCF),
		.RD(InstrF)
	);

	sumador sum_pcplus4F (
		.A(PCF),
		.B(32'd4),
		.out(PCPlus4F)
	);

	// ------------------------------------------------------------------
	// IF/ID PIPELINE REGISTER
	// ------------------------------------------------------------------
	wire [31:0] InstrD, PCD, PCPlus4D;
	wire StallD, FlushD;

	PipeReg_IF_ID mIFID (
		.clk(clk),
		.rst(rst),
		.EN(~StallD),
		.CLR(FlushD),
		.InstrF(InstrF),
		.PCF(PCF),
		.PCPlus4F(PCPlus4F),
		.InstrD(InstrD),
		.PCD(PCD),
		.PCPlus4D(PCPlus4D)
	);

	// ------------------------------------------------------------------
	// DECODE
	// ------------------------------------------------------------------
	wire RegWriteD, ALUSrcD, MemWriteD, BranchD, JumpD;
	wire [1:0] ImmSrcD, ResultSrcD, ALUOpD;
	wire [2:0] ALUControlD;

	// Declaraciones anticipadas: estas señales se generan más adelante
	// (en EX/MEM, MEM/WB y Writeback) pero se usan aquí en la
	// instanciación de RegisterFile (forwarding hacia atrás vía WB).
	wire RegWriteW;
	wire [4:0] RdW;
	wire [31:0] ResultW;
	wire [31:0] ALUResultM;

	wire [31:0] RD1D, RD2D, ImmExtD;
	wire [4:0]  Rs1D, Rs2D, RdD;

	assign Rs1D = InstrD[19:15];
	assign Rs2D = InstrD[24:20];
	assign RdD  = InstrD[11:7];

	mainDecoder mMD (
		.opcode    (InstrD[6:0]),
		.RegWrite  (RegWriteD),
		.ImmSrc    (ImmSrcD),
		.ALUSrc    (ALUSrcD),
		.MemWrite  (MemWriteD),
		.ResultSrc (ResultSrcD),
		.Branch    (BranchD),
		.ALUOp     (ALUOpD),
		.Jump      (JumpD)
	);

	ALUdecoder mALUD (
		.ALUOp  (ALUOpD),
		.op     (InstrD[5]),
		.funct3 (InstrD[14:12]),
		.funct7 (InstrD[30]),
		.Control(ALUControlD)
	);

	RegisterFile mRF (
		.clk(clk),
		.rst(rst),
		.WE3(RegWriteW),
		.A1(Rs1D),
		.A2(Rs2D),
		.A3(RdW),
		.WD3(ResultW),
		.RD1(RD1D),
		.RD2(RD2D)
	);

	extend mExt (
		.inst(InstrD),
		.ImmSrc(ImmSrcD),
		.ImmExt(ImmExtD)
	);

	// ------------------------------------------------------------------
	// ID/EX PIPELINE REGISTER
	// ------------------------------------------------------------------
	wire RegWriteE, ALUSrcE, MemWriteE, BranchE, JumpE;
	wire [1:0] ResultSrcE;
	wire [2:0] ALUControlE;

	wire [31:0] RD1E, RD2E, PCE, ImmExtE, PCPlus4E;
	wire [4:0]  Rs1E, Rs2E, RdE;
	wire FlushE;

	PipeReg_ID_EX mIDEX (
		.clk(clk),
		.rst(rst),
		.CLR(FlushE),

		.RegWriteD   (RegWriteD),
		.ResultSrcD  (ResultSrcD),
		.MemWriteD   (MemWriteD),
		.JumpD       (JumpD),
		.BranchD     (BranchD),
		.ALUControlD (ALUControlD),
		.ALUSrcD     (ALUSrcD),

		.RD1D(RD1D),
		.RD2D(RD2D),
		.PCD(PCD),
		.Rs1D(Rs1D),
		.Rs2D(Rs2D),
		.RdD(RdD),
		.ImmExtD(ImmExtD),
		.PCPlus4D(PCPlus4D),

		.RegWriteE   (RegWriteE),
		.ResultSrcE  (ResultSrcE),
		.MemWriteE   (MemWriteE),
		.JumpE       (JumpE),
		.BranchE     (BranchE),
		.ALUControlE (ALUControlE),
		.ALUSrcE     (ALUSrcE),

		.RD1E(RD1E),
		.RD2E(RD2E),
		.PCE(PCE),
		.Rs1E(Rs1E),
		.Rs2E(Rs2E),
		.RdE(RdE),
		.ImmExtE(ImmExtE),
		.PCPlus4E(PCPlus4E)
	);

	// ------------------------------------------------------------------
	// EXECUTE
	// ------------------------------------------------------------------
	wire [31:0] SrcAE, SrcBE, WriteDataE, ALUResultE, ResultW_fwd;
	wire [31:0] RegFwdA, RegFwdB;
	wire ZeroE;
	wire [1:0] ForwardAE, ForwardBE;

	// Mux de forwarding para SrcA: 00=RD1E, 01=ResultW, 10=ALUResultM
	multiplexor #(.N(3)) mux_fwdA (
		.mux_in  ({ALUResultM, ResultW, RD1E}),
		.mux_sel (ForwardAE),
		.mux_out (RegFwdA)
	);

	// Mux de forwarding para SrcB (antes del mux ALUSrc)
	multiplexor #(.N(3)) mux_fwdB (
		.mux_in  ({ALUResultM, ResultW, RD2E}),
		.mux_sel (ForwardBE),
		.mux_out (RegFwdB)
	);

	assign SrcAE = RegFwdA;
	assign WriteDataE = RegFwdB;

	// Mux ALUSrc: 0 = WriteDataE (forwardeado), 1 = ImmExtE
	multiplexor #(.N(2)) mux_alusrc (
		.mux_in  ({ImmExtE, WriteDataE}),
		.mux_sel (ALUSrcE),
		.mux_out (SrcBE)
	);

	ALU mALU (
		.A(SrcAE),
		.B(SrcBE),
		.Control(ALUControlE),
		.Result(ALUResultE),
		.Zero(ZeroE)
	);

	sumador sum_pctarget (
		.A(PCE),
		.B(ImmExtE),
		.out(PCTargetE)
	);

	BranchComparator mBC (
		.ZeroE(ZeroE),
		.BranchE(BranchE),
		.JumpE(JumpE),
		.PCSrcE(PCSrcE)
	);

	// ------------------------------------------------------------------
	// EX/MEM PIPELINE REGISTER
	// ------------------------------------------------------------------
	wire RegWriteM, MemWriteM;
	wire [1:0] ResultSrcM;
	wire [31:0] WriteDataM, PCPlus4M;
	wire [4:0] RdM;

	PipeReg_EX_MEM mEXMEM (
		.clk(clk),
		.rst(rst),

		.RegWriteE  (RegWriteE),
		.ResultSrcE (ResultSrcE),
		.MemWriteE  (MemWriteE),

		.ALUResultE (ALUResultE),
		.WriteDataE (WriteDataE),
		.RdE        (RdE),
		.PCPlus4E   (PCPlus4E),

		.RegWriteM  (RegWriteM),
		.ResultSrcM (ResultSrcM),
		.MemWriteM  (MemWriteM),

		.ALUResultM (ALUResultM),
		.WriteDataM (WriteDataM),
		.RdM        (RdM),
		.PCPlus4M   (PCPlus4M)
	);

	// ------------------------------------------------------------------
	// MEMORY
	// ------------------------------------------------------------------
	wire [31:0] ReadDataM;

	memory_RAM #(.NBits(32), .NAddr(8)) mDM (
		.clk(clk),
		.rst_a(rst),
		.wr_en(MemWriteM),
		.Data_in(WriteDataM),
		.Data_address(ALUResultM[7:0]),
		.Data_out(ReadDataM)
	);

	// ------------------------------------------------------------------
	// MEM/WB PIPELINE REGISTER
	// ------------------------------------------------------------------
	wire [1:0] ResultSrcW;
	wire [31:0] ALUResultW, ReadDataW, PCPlus4W;

	PipeReg_MEM_WB mMEMWB (
		.clk(clk),
		.rst(rst),

		.RegWriteM  (RegWriteM),
		.ResultSrcM (ResultSrcM),

		.ALUResultM (ALUResultM),
		.ReadDataM  (ReadDataM),
		.RdM        (RdM),
		.PCPlus4M   (PCPlus4M),

		.RegWriteW  (RegWriteW),
		.ResultSrcW (ResultSrcW),

		.ALUResultW (ALUResultW),
		.ReadDataW  (ReadDataW),
		.RdW        (RdW),
		.PCPlus4W   (PCPlus4W)
	);

	// ------------------------------------------------------------------
	// WRITEBACK
	// ------------------------------------------------------------------
	// ResultSrcW: 00 = ALUResultW, 01 = ReadDataW, 10 = PCPlus4W
	multiplexor #(.N(3)) mux_resultw (
		.mux_in  ({PCPlus4W, ReadDataW, ALUResultW}),
		.mux_sel (ResultSrcW),
		.mux_out (ResultW)
	);

	// ------------------------------------------------------------------
	// HAZARD UNIT
	// ------------------------------------------------------------------
	HazardUnit mHU (
		.Rs1D(Rs1D),
		.Rs2D(Rs2D),
		.Rs1E(Rs1E),
		.Rs2E(Rs2E),
		.RdE(RdE),
		.RdM(RdM),
		.RdW(RdW),

		.RegWriteM(RegWriteM),
		.RegWriteW(RegWriteW),
		.ResultSrcE0(ResultSrcE[0]),
		.PCSrcE(PCSrcE),

		.StallF(StallF),
		.StallD(StallD),
		.FlushD(FlushD),
		.FlushE(FlushE),
		.ForwardAE(ForwardAE),
		.ForwardBE(ForwardBE)
	);

endmodule
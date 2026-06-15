module BranchComparator (
    input  ZeroE,
    input  BranchE,
    input  JumpE,
    output PCSrcE
);

	assign PCSrcE = (ZeroE & BranchE) | JumpE;

endmodule
// Main decoder input opcode, output: L-type, S-type, R-type, B-type, I-type, J-type
module main_decoder(
    input[6:0]op,
    output reg[1:0] ResultSrc,
    output reg MemWrite, Branch, ALUSrc, RegWrite, Jump,
    output reg [1:0] ImmSrc,
    output reg [1:0] ALUOp
);

    parameter
        Ltype = 7'b0000011, //load
        Itype = 7'b0010011, //i
        Stype = 7'b0100011, //store
        Rtype = 7'b0110011, //R
        Btype = 7'b1100011, //branch
        Jtype = 7'b1101111; //J

    always @(*) begin
        casex (op)
            Ltype: begin
                RegWrite = 1;
                ImmSrc = 2'b00;
                ALUSrc = 1;
                MemWrite = 0; 
                ResultSrc = 2'b01;
                Branch = 0; 
                ALUOp =2'b00;
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
            Stype: begin
                RegWrite = 0;
                ImmSrc = 2'b01;
                ALUSrc = 1;
                MemWrite = 1; 
                ResultSrc = 2'b00;
                Branch = 0; 
                ALUOp =2'b00;
                Jump = 0;
                
            end
            Rtype: begin
                RegWrite = 1;
                ImmSrc = 2'bxx;
                ALUSrc = 0;
                MemWrite = 0; 
                ResultSrc = 2'b00;
                Branch = 0; 
                ALUOp =2'b10;
                Jump = 0;
             
            end
            Btype: begin
                RegWrite = 0;
                ImmSrc = 2'b10;
                ALUSrc = 0;
                MemWrite = 0;
                ResultSrc = 2'bxx;
                Branch = 1;
                ALUOp =2'b01;
                Jump = 0;
                
            end
            
            Jtype: begin
                RegWrite = 1;
                ImmSrc = 2'b11;
                ALUSrc = 1'bx;
                MemWrite = 0; 
                ResultSrc = 2'b10;
                Branch = 0;
                ALUOp =2'bxx;
                Jump = 1;
                
            end
        default: begin
            RegWrite = 0;
            ImmSrc = 2'b00;
            ALUSrc = 0;
            MemWrite = 0; 
            ResultSrc = 2'b00;
            Branch = 0;
            ALUOp =2'b00;
            Jump = 0;
            
        end
        endcase
    end
endmodule

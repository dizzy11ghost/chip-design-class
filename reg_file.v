module reg_file(
    input clk, WE3, 
    input [4:0] A1,
    input [4:0] A2,
    input [4:0] A3,
    input [31:0] WD3,
    output [31:0] RD1,
    output [31:0] RD2
);
reg[31:0] r_file [31:0]; //32 registros 32 bits

initial begin
    r_file[0] = 32'b0;
end

assign RD1 = (A1 == 0) ? 32'b0 : r_file[A1]; //el registro devuelve lo qey haya en A1 (a menos que sea 0)
assign RD2 = (A2 == 0) ? 32'b0 : r_file[A2];

always@(posedge clk) //escritura registros
    begin
    if(WE3 == 1 && A3 != 0) //si WE3 es 1 y el registro no es 0, escribimos en el registro A3 el valor de WD3
        r_file[A3] <= WD3;
    end
endmodule
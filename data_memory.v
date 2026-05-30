module data_memory #(parameter NBits = 32)(
	input clk, rst, WE, //write enable 
	input [NBits - 1 : 0] A, //address of data input
	input [NBits - 1 : 0] WD, //write data (data input)
	output reg [NBits - 1 : 0] RD //read data output
);

reg [NBits - 1 : 0] RAM [0:7]; 

//Consultar con Gonzaloooooo
always @(posedge clk) begin
	if(WE == 1) begin
		if (A[31:2] <= 7) 
			RAM[A[31:2]] <= WD;
	end
end

always @(*) begin
	RD = RAM[A[31:2]];
end

endmodule 

//usamos 31:2 porque cada palabra tiene 4 bytes, entonces los 2 bits menos significativos se usan para direccionar dentro de la palabra, y el resto se usa para direccionar las palabras en la memoria

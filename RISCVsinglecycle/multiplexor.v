module multiplexor #(parameter N = 2) (
    input [N*32-1:0] mux_in,
    input [$clog2(N)-1:0] mux_sel, //saca el logaritmo base 2 para saber cuántos bits 
    output [31:0] mux_out
);

assign mux_out = mux_in[mux_sel*32 +: 32]; //seleccionamos el bloque de 32 bits correspondiente al valor de mux_sel
 
endmodule

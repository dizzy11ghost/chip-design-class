module multiplexor #(parameter N = 2) (
    input  [N*32-1:0]        mux_in,
    input  [$clog2(N)-1:0]   mux_sel,
    output reg [31:0]        mux_out
);
    always @(*)
        mux_out = mux_in[(mux_sel*32) +: 32]; 

endmodule
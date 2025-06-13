module serial_multiplier (
    input logic clk,
    input logic rst,
    input logic start,
    input logic [3:0] A,
    input logic [3:0] B,
    output logic [7:0] result,
    output logic done
);
    typedef enum logic [1:0] {IDLE, RUN, DONE} state_t;
    state_t state;

    logic [3:0] regA, regB;
    logic [7:0] regResult;
    logic [3:0] count;

    always_ff @(posedge clk or posedge rst) begin
        if (rst) begin
            state <= IDLE;
            regA <= 0;
            regB <= 0;
            regResult <= 0;
            count <= 0;
            done <= 0;
        end else begin
            case (state)
                IDLE: begin
                    done <= 0;
                    if (start) begin
                        regA <= A;
                        regB <= B;
                        regResult <= 0;
                        count <= 4;
                        state <= RUN;
                    end
                end
                RUN: begin
                    if (regA[0]) begin
                        regResult <= regResult + {4'b0, regB};
                    end
                    regA <= regA >> 1;
                    regB <= regB << 1;
                    count <= count - 1;
                    if (count == 1)
                        state <= DONE;
                end
                DONE: begin
                    done <= 1;
                    result <= regResult;
                    state <= IDLE;
                end
            endcase
        end
    end

`ifdef COCOTB_SIM
    initial begin
        $dumpfile("sim_build/serial_multiplier.vcd");
        $dumpvars(0, serial_multiplier);
    end
`endif

endmodule

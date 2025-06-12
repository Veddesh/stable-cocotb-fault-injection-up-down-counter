TOPLEVEL_LANG = verilog
VERILOG_SOURCES := $(shell pwd)/counter.v
TOPLEVEL = counter
MODULE = counter_tb
SIM = icarus

WAVES=1
YOSYS_JSON := $(shell pwd)/yosys.json
export YOSYS_JSON

export PYTHONPATH := $(shell pwd):$(PYTHONPATH)

all: yosys run

yosys:
	yosys -p "read_verilog -sv counter.v; proc; opt; write_json yosys.json"

run:
	$(MAKE) -f $(shell cocotb-config --makefiles)/Makefile.sim \
		MODULE=$(MODULE) \
		TOPLEVEL=$(TOPLEVEL) \
		TOPLEVEL_LANG=$(TOPLEVEL_LANG) \
		SIM=$(SIM) \
		VERILOG_SOURCES="$(VERILOG_SOURCES)"

clean:
	rm -rf sim_build __pycache__ results.xml *.vcd *.json

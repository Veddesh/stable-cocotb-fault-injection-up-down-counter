import cocotb
from cocotb.triggers import Timer, RisingEdge, FallingEdge
from cocotb.clock import Clock
import logging

from cocotb_fault_injection import (
    HierarchyFaultInjector,
    RandomInjectionStrategy,
    BoundedRandomTimer,
    SEEsPerNode
)


class CounterTestbench:
    def __init__(self, dut):
        self.dut = dut
        self.expected = []
        self.actual = []

    async def reset(self):
        self.dut.rst.value = 1
        await Timer(1, units='ns')
        await RisingEdge(self.dut.clk)
        await FallingEdge(self.dut.clk)
        self.dut.rst.value = 0
        self.dut._log.info("Reset complete.")

    async def check_count(self, cycles=64):
        for i in range(cycles):  # Check N counter cycles
            await RisingEdge(self.dut.clk)
            expected_val = i % 256
            actual_val = int(self.dut.count.value)
            self.expected.append(expected_val)
            self.actual.append(actual_val)

            self.dut._log.info(f"Cycle {i}: Expected={expected_val}, Actual={actual_val}")
            assert expected_val == actual_val, f"Mismatch in output at cycle {i}"


@cocotb.test()
async def counter_test(dut):
    dut._log.info("Running test!")

    # Start 25 ns clock
    cocotb.start_soon(Clock(dut.clk, 25, units='ns').start())

    tb = CounterTestbench(dut)
    await tb.reset()

    # ✅ Configure fault injector to inject SEUs (persistent bit flips)
    seugen = HierarchyFaultInjector(
        root=dut,
        exclude_names=["rst", "clk"],
        mttf_timer=BoundedRandomTimer(mttf_min=100, mttf_max=300, units="ns"),
        transient_duration_timer=None,  # ⛔ No transient flip-back (SEU mode)
        injection_strategy=RandomInjectionStrategy(),
        injection_goal=SEEsPerNode(5),  # More aggressive
        log_level=logging.DEBUG
    )

    # ✅ Run test + injection in parallel
    injector_task = cocotb.start_soon(seugen.start())
    monitor_task = cocotb.start_soon(tb.check_count(cycles=64))  # monitor 64 cycles

    await monitor_task  # will raise assertion on fault effect

    # Let faults continue a bit more (optional)
    await Timer(2000, units="ns")
    seugen.stop()
    await injector_task

    dut._log.info("Finished test.")
    seugen.print_summary()

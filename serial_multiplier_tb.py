import cocotb
from cocotb.triggers import RisingEdge, Timer
from cocotb.clock import Clock
from cocotb.result import TestFailure
from cocotb.log import SimLog
from cocotb_fault_injection import (
    HierarchyFaultInjector,
    BoundedRandomTimer,
    SEEsPerNode,
    RandomInjectionStrategy
)

log = SimLog("cocotb.serial_multiplier")

@cocotb.test()
async def multiplier_test(dut):
    log.info("🔢 Starting Serial Multiplier Test")
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # Reset
    dut.rst.value = 1
    dut.start.value = 0
    await Timer(25, units="ns")
    dut.rst.value = 0

    # Inject faults after some time
    seugen = HierarchyFaultInjector(
        root=dut,
        exclude_names=["clk", "rst"],
        mttf_timer=BoundedRandomTimer(mttf_min=200, mttf_max=400, units="ns"),
        transient_duration_timer=None,
        injection_strategy=RandomInjectionStrategy(),
        injection_goal=SEEsPerNode(5),
        log_level="DEBUG"
    )
    cocotb.start_soon(seugen.start())

    # Run test
    test_vectors = [(4, 9), (0, 5), (10, 4), (5, 13)]
    for a, b in test_vectors:
        log.info(f"🔁 Testing A={a} B={b}, expecting result={a * b}")
        dut.A.value = a
        dut.B.value = b
        dut.start.value = 1
        await RisingEdge(dut.clk)
        dut.start.value = 0

        for _ in range(100):
            await RisingEdge(dut.clk)
            if dut.done.value == 1:
                actual = dut.result.value.integer
                expected = a * b
                log.info(f"✅ Done. Expected={expected}, Actual={actual}")
                if actual != expected:
                    log.warning(f"⚠️ Mismatch detected: result={actual}, expected={expected}")
                break
        await Timer(100, units="ns")

    await seugen.join()
    seugen.print_summary()

# MIPS Architecture Simulator

## Overview

This project implements a **5-stage pipelined MIPS processor simulator** with two architectural enhancements:

1. **Delayed Branch Execution** — eliminates pipeline flushes by introducing a branch delay slot.
2. **Multi-Cycle Memory Access** — simulates variable memory latency (2–3 cycles) for load/store operations.

The simulator is written in **Python** and models each pipeline stage (IF, ID, EX, MEM, WB) step-by-step. It provides
 detailed logs of instruction flow, stalls, hazards, and performance metrics.

## Features

- 5-stage pipeline (IF, ID, EX, MEM, WB)
- Delayed branch execution (branch delay slot)
- Configurable multi-cycle memory latency for loads/stores (2–3 cycles)
- Per-cycle pipeline tracing, stalls, and hazard reporting

## Files

- `main.py` — simulator entry point / runner
- `instruction.py` — instruction definitions and helpers
- `parser.py` — assembler/parser for `sample.asm`
- `memory.py` — memory model with multi-cycle delays
- `pipeline_registers.py` — pipeline stage registers and movement logic
- `registers.py` — architectural register file
- `sample.asm` — example MIPS assembly for testing
- `MIPS_Processor_Simulation_Report.pdf` — project report

## Quick usage

1. Install Python 3.8+ (recommended).
2. From the project root run:

```powershell
python main.py
```

The simulator will run the sample program and print per-cycle logs and a summary of performance metrics.


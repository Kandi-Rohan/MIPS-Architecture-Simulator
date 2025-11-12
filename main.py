print("Loading main.py")

import random
from registers import RegisterFile
from memory import Memory
from pipeline_registers import PipelineRegister
from parser import parse_instruction

class MIPSSimulator:
    def __init__(self):
        self.regs = RegisterFile()
        self.mem = Memory()
        self.pc = 0
        self.cycle_count = 0
        self.stall_count = 0
        self.instruction_count = 0

        # Pipeline registers
        self.IF_ID = PipelineRegister()
        self.ID_EX = PipelineRegister()
        self.EX_MEM = PipelineRegister()
        self.MEM_WB = PipelineRegister()

        # Statistics
        self.load_stalls = 0
        self.memory_delay_cycles = 0
        self.branch_delay_effective = 0
        self.branch_delay_total = 0
        self.data_hazard_stalls = 0

        # Control signals
        self.stall = False
        self.memory_stall = False
        self.branch_target = None
        self.branch_delay_active = False

    def load_program(self):
        instructions = []
        labels = {}
        try:
            with open('sample.asm', 'r') as f:
                content = f.read().replace('\r\n', '\n').replace('\r', '\n')
                lines = content.split('\n')
                print(f"Read {len(lines)} lines from sample.asm")
        except FileNotFoundError:
            print("Error: sample.asm not found")
            return
        except Exception as e:
            print(f"Error reading sample.asm: {e}")
            return

        # collect labels
        instruction_count = 0
        for i, line in enumerate(lines):
            line = line.strip()
            print(f"Processing line {i+1}: {line}")
            if not line:
                continue
            if line.endswith(':'):
                labels[line[:-1]] = instruction_count
                print(f"Found label: {line[:-1]} at instruction {instruction_count}")
            elif not line.startswith('.'):
                instructions.append(line)
                instruction_count += 1

        # parse instructions
        self.program = []
        for line in instructions:
            if not line:
                continue
            parse_line = line.split('#')[0].strip()
            if not parse_line:
                continue
            instr = parse_instruction(parse_line, labels)
            if instr.opcode is not None:  
                instr.source_line = line
                self.program.append(instr)
                print(f"Parsed instruction: {parse_line} -> opcode={instr.opcode}")
            else:
                print(f"Skipping invalid instruction: {parse_line}")
        self.program_length = len(self.program)
        print(f"Loaded {self.program_length} instructions")
        if not self.program:
            print("Error: No valid instructions loaded")

    def check_data_hazard(self):
        if not self.ID_EX.valid or not self.ID_EX.instr:
            return False

        inst = self.ID_EX.instr
        src_regs = [inst.rs, inst.rt] if inst.opcode != 'sw' else [inst.rs]
        src_regs = [r for r in src_regs if r is not None and r != 0]

        # Stall for load-use hazards
        if self.EX_MEM.valid and self.EX_MEM.dest_reg in src_regs and self.EX_MEM.instr.opcode == 'lw':
            return True
        return False

    def forward_data(self):
        if not self.ID_EX.valid or not self.ID_EX.instr:
            return

        inst = self.ID_EX.instr
        if inst.rs and inst.rs != 0:
            if self.EX_MEM.valid and self.EX_MEM.dest_reg == inst.rs and self.EX_MEM.instr.opcode != 'lw':
                self.ID_EX.rs_value = self.EX_MEM.alu_result
            elif self.MEM_WB.valid and self.MEM_WB.dest_reg == inst.rs:
                self.ID_EX.rs_value = self.MEM_WB.mem_result
        if inst.rt and inst.rt != 0 and inst.opcode != 'sw':
            if self.EX_MEM.valid and self.EX_MEM.dest_reg == inst.rt and self.EX_MEM.instr.opcode != 'lw':
                self.ID_EX.rt_value = self.EX_MEM.alu_result
            elif self.MEM_WB.valid and self.MEM_WB.dest_reg == inst.rt:
                self.ID_EX.rt_value = self.MEM_WB.mem_result

    def fetch(self):
        if not (self.stall or self.memory_stall) and self.pc < self.program_length:
            self.IF_ID.instr = self.program[self.pc]
            self.IF_ID.valid = True
            self.pc += 1
            print(f"Fetched instruction at PC {self.pc-1}: {self.IF_ID.instr.opcode}")
        else:
            self.IF_ID.instr = None
            self.IF_ID.valid = False

    def decode(self):
        if self.stall or self.memory_stall:
            self.ID_EX.instr = None
            self.ID_EX.valid = False
            return

        if self.check_data_hazard():
            self.stall = True
            self.data_hazard_stalls += 1
            self.ID_EX.instr = None
            self.ID_EX.valid = False
            print("Stall due to data hazard")
            return

        if self.IF_ID.valid and self.IF_ID.instr:
            self.ID_EX.instr = self.IF_ID.instr
            self.ID_EX.valid = True

            # Read register values with error handling
            inst = self.ID_EX.instr
            try:
                if inst.rs is not None:
                    self.ID_EX.rs_value = self.regs.read(inst.rs)
                if inst.rt is not None:
                    self.ID_EX.rt_value = self.regs.read(inst.rt)
            except ValueError as e:
                print(f"Error reading register: {e}")
                self.ID_EX.instr = None
                self.ID_EX.valid = False
                return

            # Set destination register
            self.ID_EX.dest_reg = inst.rd if inst.opcode in ['add', 'sub'] else inst.rt if inst.opcode in ['lw', 'addi'] else None
            print(f"Decoded instruction: {inst.opcode}, dest_reg={self.ID_EX.dest_reg}")

            # Check for branch
            if inst.opcode == 'beq':
                self.branch_delay_active = True
                if self.ID_EX.rs_value == self.ID_EX.rt_value:
                    self.branch_target = inst.immediate
                    if self.branch_target >= self.program_length:
                        self.branch_target = self.program_length
                    print(f"Branch taken to PC {self.branch_target}")
                else:
                    self.branch_target = self.pc  # Continue with next instruction
                    print("Branch not taken")
        else:
            self.ID_EX.instr = None
            self.ID_EX.valid = False

        self.forward_data()

    def execute(self):
        if self.stall or self.memory_stall:
            self.EX_MEM.instr = None
            self.EX_MEM.valid = False
            return

        if self.ID_EX.valid and self.ID_EX.instr:
            self.EX_MEM.instr = self.ID_EX.instr
            self.EX_MEM.valid = True
            self.EX_MEM.dest_reg = self.ID_EX.dest_reg

            inst = self.EX_MEM.instr
            if inst.opcode == 'add':
                self.EX_MEM.alu_result = self.ID_EX.rs_value + self.ID_EX.rt_value
            elif inst.opcode == 'sub':
                self.EX_MEM.alu_result = self.ID_EX.rs_value - self.ID_EX.rt_value
            elif inst.opcode == 'addi':
                self.EX_MEM.alu_result = self.ID_EX.rs_value + inst.immediate
            elif inst.opcode in ['lw', 'sw']:
                self.EX_MEM.alu_result = self.ID_EX.rs_value + inst.immediate
                self.EX_MEM.cycles_remaining = random.choice([2, 3])
            elif inst.opcode == 'beq':
                self.EX_MEM.alu_result = 0  
            print(f"Executed instruction: {inst.opcode}, alu_result={self.EX_MEM.alu_result}")
        else:
            self.EX_MEM.instr = None
            self.EX_MEM.valid = False

    def memory(self):
        if self.EX_MEM.valid and hasattr(self.EX_MEM, 'cycles_remaining') and self.EX_MEM.cycles_remaining > 0:
            self.EX_MEM.cycles_remaining -= 1
            self.memory_stall = True
            self.memory_delay_cycles += 1
            if self.EX_MEM.instr.opcode == 'lw':
                self.load_stalls += 1
            print(f"Memory stall: {self.EX_MEM.instr.opcode}, cycles remaining={self.EX_MEM.cycles_remaining}")
            return

        self.memory_stall = False
        if self.EX_MEM.valid and self.EX_MEM.instr:
            inst = self.EX_MEM.instr
            self.MEM_WB.instr = inst
            self.MEM_WB.valid = True
            self.MEM_WB.dest_reg = self.EX_MEM.dest_reg

            if inst.opcode == 'lw':
                self.MEM_WB.mem_result = self.mem.load(self.EX_MEM.alu_result)
            elif inst.opcode == 'sw':
                self.mem.store(self.EX_MEM.alu_result, self.ID_EX.rt_value)
                self.instruction_count += 1  
                self.MEM_WB.valid = False  
            elif inst.opcode in ['add', 'sub', 'addi']:
                self.MEM_WB.mem_result = self.EX_MEM.alu_result
            elif inst.opcode == 'beq':
                self.instruction_count += 1  
                self.MEM_WB.valid = False  
            print(f"Memory stage: {inst.opcode}, mem_result={self.MEM_WB.mem_result if self.MEM_WB.valid else 'N/A'}")
            self.EX_MEM.instr = None
            self.EX_MEM.valid = False 
        else:
            self.MEM_WB.instr = None
            self.MEM_WB.valid = False

        self.stall = False

    def writeback(self):
        if self.MEM_WB.valid and self.MEM_WB.instr:
            inst = self.MEM_WB.instr
            if inst.opcode in ['add', 'sub']:
                self.regs.write(inst.rd, self.MEM_WB.mem_result)
                self.instruction_count += 1
            elif inst.opcode in ['lw', 'addi']:
                self.regs.write(inst.rt, self.MEM_WB.mem_result)
                self.instruction_count += 1
            print(f"Writeback: {inst.opcode}, dest_reg={self.MEM_WB.dest_reg}, value={self.MEM_WB.mem_result}")
            self.MEM_WB.instr = None
            self.MEM_WB.valid = False  

    def run_cycle(self):
        print(f"Cycle {self.cycle_count}:")
        print(f"IF: {self.IF_ID.instr.opcode if self.IF_ID.valid and self.IF_ID.instr else 'NOP'}")
        print(f"    Source: {self.IF_ID.instr.source_line if self.IF_ID.valid and self.IF_ID.instr else 'N/A'}")
        print(f"ID: {self.ID_EX.instr.opcode if self.ID_EX.valid and self.ID_EX.instr else 'NOP'}")
        print(f"    Source: {self.ID_EX.instr.source_line if self.ID_EX.valid and self.ID_EX.instr else 'N/A'}")
        print(f"EX: {self.EX_MEM.instr.opcode if self.EX_MEM.valid and self.EX_MEM.instr else 'NOP'}")
        print(f"    Source: {self.EX_MEM.instr.source_line if self.EX_MEM.valid and self.EX_MEM.instr else 'N/A'}")
        print(f"MEM: {self.MEM_WB.instr.opcode if self.MEM_WB.valid and self.MEM_WB.instr else 'NOP'}")
        print(f"     Source: {self.MEM_WB.instr.source_line if self.MEM_WB.valid and self.MEM_WB.instr else 'N/A'}")
        print(f"WB: {'Completed' if self.MEM_WB.valid else 'NOP'}")
        print("-" * 50)

        if self.stall or self.memory_stall:
            self.stall_count += 1

        self.writeback()
        self.memory()
        self.execute()
        self.decode()
        self.fetch()

        if self.branch_delay_active:
            self.branch_delay_total += 1
            self.branch_delay_effective += 1  
            if self.branch_target is not None:
                self.pc = self.branch_target
                self.branch_target = None
                self.IF_ID.instr = None
                self.IF_ID.valid = False
                print(f"Branch applied: PC set to {self.pc}")
            self.branch_delay_active = False

        self.cycle_count += 1

    def run(self):
        # Fetch first instruction immediately
        if self.program_length > 0:
            self.fetch()
            self.cycle_count = 0

        # Run until all instructions are fetched and pipeline is empty
        while self.pc < self.program_length or any([self.IF_ID.valid, self.ID_EX.valid, self.EX_MEM.valid, self.MEM_WB.valid]):
            if self.cycle_count > 100:  
                print("Error: Simulation exceeded 100 cycles, possible infinite loop")
                break
            self.run_cycle()

        cpi = self.cycle_count / self.instruction_count if self.instruction_count > 0 else 0
        print(f"Total Clock Cycles: {self.cycle_count}")
        print(f"Total Instructions Executed: {self.instruction_count}")
        print(f"Cycles Per Instruction (CPI): {cpi:.2f}")
        print(f"Total Stalls: {self.stall_count}")
        print(f"Load Stalls: {self.load_stalls}")
        print(f"Data Hazard Stalls: {self.data_hazard_stalls}")
        print(f"Memory Delay Cycles: {self.memory_delay_cycles}")
        print(f"Branch Delay Slot Effectiveness: {self.branch_delay_effective}/{self.branch_delay_total}")

def main():
    sim = MIPSSimulator()
    sim.load_program()
    sim.run()

if __name__ == "__main__":
    main()
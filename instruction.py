class Instruction:
    def __init__(self, opcode, rs, rt, rd, immediate=None):
        self.opcode = opcode
        self.rs = rs
        self.rt = rt
        self.rd = rd
        self.immediate = immediate

    def __str__(self):
        return f"{self.opcode} {self.rs} {self.rt} {self.rd} {self.immediate}"

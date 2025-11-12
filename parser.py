print("Loading parser.py with updated reg_map")

class Instruction:
    def __init__(self, opcode, rs, rt, rd, immediate=None, target=None, source_line=None):
        self.opcode = opcode
        self.rs = rs
        self.rt = rt
        self.rd = rd
        self.immediate = immediate
        self.target = target
        self.source_line = source_line

def parse_instruction(line, labels=None):
    print(f"Parsing line: {line}")
    line = line.strip().split('#')[0].strip()
    if not line or line.startswith(".") or line == "nop":
        return Instruction(None, None, None, None)

    tokens = line.replace(',', ' ').replace('(', ' ').replace(')', ' ').split()
    if not tokens:
        return Instruction(None, None, None, None)

    opcode = tokens[0].lower()
    reg_map = {
        '$zero': 0, '$0': 0,
        '$t0': 8, '$t1': 9, '$t2': 10, '$t3': 11,
        '$t4': 12, '$t5': 13, '$t6': 14, '$t7': 15,
        '$s0': 16, '$s1': 17, '$s2': 18, '$s3': 19,
        '$s4': 20, '$s5': 21, '$s6': 22, '$s7': 23,
        '$t8': 24, '$t9': 25,
        '$a0': 4, '$a1': 5, '$a2': 6, '$a3': 7,
        '$v0': 2, '$v1': 3,
        '$gp': 28, '$sp': 29, '$fp': 30, '$ra': 31,
        '$at': 1, '$k0': 26, '$k1': 27
    }

    try:
        if opcode in ["lw", "sw"]:
            rt = reg_map.get(tokens[1].strip(',').lower(), None)
            offset = int(tokens[2])
            rs = reg_map.get(tokens[3].strip(',').lower(), None)
            if None in [rt, rs]:
                raise ValueError(f"Invalid register in {tokens}")
            return Instruction(opcode, rs, rt, None, offset)

        elif opcode in ["add", "sub"]:
            rd = reg_map.get(tokens[1].strip(',').lower(), None)
            rs = reg_map.get(tokens[2].strip(',').lower(), None)
            rt = reg_map.get(tokens[3].strip(',').lower(), None)
            if None in [rd, rs, rt]:
                raise ValueError(f"Invalid register in {tokens}")
            return Instruction(opcode, rs, rt, rd)

        elif opcode == "beq":
            rs = reg_map.get(tokens[1].strip(',').lower(), None)
            rt = reg_map.get(tokens[2].strip(',').lower(), None)
            if None in [rs, rt]:
                raise ValueError(f"Invalid register in {tokens}")
            target = labels.get(tokens[3], 0) if labels else 0
            return Instruction(opcode, rs, rt, None, target)

        elif opcode == "addi":
            rt = reg_map.get(tokens[1].strip(',').lower(), None)
            rs = reg_map.get(tokens[2].strip(',').lower(), None)
            if None in [rt, rs]:
                raise ValueError(f"Invalid register in {tokens}")
            immediate = int(tokens[3])
            return Instruction(opcode, rs, rt, None, immediate)

        return Instruction(None, None, None, None)
    except (IndexError, ValueError) as e:
        print(f"Error parsing instruction: {line} ({str(e)})")
        return Instruction(None, None, None, None)
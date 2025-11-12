class RegisterFile:
    def __init__(self):
        # Initialize 32 registers (0 to 31), all set to 0
        self.registers = {i: 0 for i in range(32)}
        self.registers[0] = 0  # Ensure $zero is always 0

    def read(self, reg_num):
        if reg_num not in self.registers:
            raise ValueError(f"Register {reg_num} not found")
        return self.registers[reg_num]

    def write(self, reg_num, value):
        if reg_num == 0:
            return  
        if reg_num not in self.registers:
            raise ValueError(f"Register {reg_num} not found")
        self.registers[reg_num] = value
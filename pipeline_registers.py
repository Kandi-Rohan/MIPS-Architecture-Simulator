class PipelineRegister:
    def __init__(self):
        self.instr = None
        self.valid = False
        self.rs_value = None
        self.rt_value = None
        self.alu_result = None
        self.mem_result = None
        self.dest_reg = None
        self.cycles_remaining = 0
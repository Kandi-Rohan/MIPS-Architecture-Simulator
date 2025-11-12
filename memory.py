class Memory:
    def __init__(self):
        self.memory = {}
        # Initialize memory with test values
        for i in range(0, 100, 4):
            self.memory[i] = i * 2  
    def load(self, address):
        return self.memory.get(address, 0)

    def store(self, address, value):
        self.memory[address] = value
class DebugOutput:
    def __init__(self, output_fn: str = 'debug.out'):
        self.entries = list()
        self.output_fn = output_fn
    def add_str(self, entry):
        self.entries.append(str(len(self.entries)) +': ' + entry + '\n\n')
    def to_file(self):
        with open(self.output_fn, 'w', encoding='utf-8') as fn:
            fn.writelines(self.entries)
    def get_entries(self):
        return self.entries
            
    
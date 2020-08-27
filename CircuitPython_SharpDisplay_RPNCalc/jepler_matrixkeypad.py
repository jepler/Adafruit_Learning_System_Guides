import digitalio
import microcontroller

def get_pin(x):
    if isinstance(x, microcontroller.Pin):
        return digitalio.DigitalInOut(x)
    return x

class MatrixKeypadBase:
    def __init__(self, row_pins, col_pins):
        self.row_pins = [get_pin(p) for p in row_pins]
        self.col_pins = [get_pin(p) for p in col_pins]
        self.old_state = set()
        self.state = set()

        for r in self.row_pins:
            r.switch_to_input(digitalio.Pull.UP)
        for c in self.col_pins:
            c.switch_to_output(False)

    def scan(self):
        self.old_state = self.state
        state = set()
        for c, cp in enumerate(self.col_pins):
            cp.switch_to_output(False)
            for r, rp in enumerate(self.row_pins):
                if not rp.value:
                    state.add((r, c))
            cp.switch_to_input()
        self.state = state
        return state

    def rising(self):
        old_state = self.old_state
        new_state = self.state

        return new_state - old_state

class LayerSelect:
    def __init__(self, idx=1, next_layer=None):
        self.idx = idx
        self.next_layer = next_layer or self

LL0 = LayerSelect(0)
LL1 = LayerSelect(1)
LS1 = LayerSelect(1, LL0)

class MatrixKeypad:
    def __init__(self, row_pins, col_pins, layers):
        self.base = MatrixKeypadBase(row_pins, col_pins)
        self.layers = layers
        self.layer = LL0
        self.pending = []
 
    def getch(self):
        if not self.pending:
            self.base.scan()
            for r, c in self.base.rising():
                op = self.layers[self.layer.idx][r][c]
                if isinstance(op, LayerSelect):
                    self.layer = op
                else:
                    self.pending.extend(op)
                    self.layer = self.layer.next_layer

        if self.pending:
            return self.pending.pop(0)

        return None

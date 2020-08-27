import sys
import math

if sys.implementation.name == 'cpython':
    from calc_desktop import Impl
elif sys.implementation.name == 'circuitpython':
    from calc_circuitpython import Impl
impl = Impl()

stack = []
entry = []

def do_op(arity, fun):
    if arity > len(stack):
        return "underflow"
    res = fun(*stack[-arity:])
    del stack[-arity:]
    if isinstance(res, list):
        stack.extend(res)
    elif res is not None:
        stack.append(res)

class AngleConvert:
    def __init__(self):
        self.state = 0

    def next_state(self):
        self.state = (self.state + 1) % 3

    def __str__(self):
        return "DRG"[self.state]

    @property
    def factor(self):
        return [math.pi/180, 1, math.pi/200][self.state]

    def from_r(self, x):
        return x * self.factor

    def to_r(self, x):
        return x / self.factor

angleconvert = AngleConvert()

def ACOS(x): return angleconvert.to_r(math.acos(x))
def ASIN(x): return angleconvert.to_r(math.asin(x))
def ATAN(x): return angleconvert.to_r(math.atan(x))
def COS(x): return math.cos(angleconvert.from_r(x))
def SIN(x): return math.sin(angleconvert.from_r(x))
def TAN(x): return math.tan(angleconvert.from_r(x))

def roll():
    stack[:] = stack[1:] + stack[:1]

def rroll():
    stack[:] = stack[-1:] + stack[:-1]

def swap():
    stack[-2:] = [stack[-1], stack[-2]]

ops = {
    '\'': (1, lambda x: -x),
    '\\': (2, lambda y, x: y/x),  # keypad: SHIFT+/
    '#': (2, lambda y, x: x**(1/y)),  # keypad: SHIFT-^
    '*': (2, lambda y, x: x*y),
    '+': (2, lambda y, x: x+y),
    '-': (2, lambda y, x: x-y),
    '/': (2, lambda y, x: x/y),
    '^': (2, lambda y, x: y**x),
    'v': (2, lambda y, x: y**(1/x)),
    '_': (2, lambda y, x: x-y),   # keypad: SHIFT+-
    '@': angleconvert.next_state,
    'C': (1, ACOS),
    'c': (1, COS),
    'L': (1, math.exp),
    'l': (1, math.log),
    'q': (1, lambda x: x**.5),
    'r': roll,                    # keypad: shift-SWAP
    'R': rroll,
    'S': (1, ASIN),
    's': (1, SIN),
    '~': swap,
    'T': (1, ATAN),
    't': (1, TAN),
    'n': (1, lambda x: -x),
    'N': (1, lambda x: 1/x),
    '=': lambda: impl.paste(stack[-1]),
}

def pstack(msg):
    impl.setline(0, f'[{angleconvert}] {msg}')

    for i, reg in enumerate("TZYX"):
        if len(stack) > 3-i:
            val = stack[-4+i]
        else:
            val = ""
        impl.setline(1+i, f"{reg}: {val}")

def loop():
    pstack('')
    impl.setline(5, ">>> " + "".join(entry) + "_")
    impl.refresh()

    while True:
        do_pstack = False
        do_pentry = False
        message = ''


        c = impl.getch()
        if c in '\x7f\x08':
            if entry:
                entry.pop()
                do_pentry = True
            elif stack:
                stack.pop()
                do_pstack = True
        if c == '\x1b':
            del entry[:]
            do_pentry = True
        elif c in '0123456789.eE':
            if c == '.' and '.' in entry:
                c = 'e'
            entry.append(c)
            do_pentry = True
        elif c == '\x04':
            break
        elif c in ' \n':
            if entry:
                stack.append(float("".join(entry)))
                del entry[:]
            elif c == '\n' and stack:
                stack.append(stack[-1])
            do_pstack = True
        elif c in ops:
            if entry:
                try:
                    stack.append(float("".join(entry)))
                except ValueError as e:
                    message = str(e)
                del entry[:]
            op = ops.get(c)
            try:
                if callable(op):
                    message = op() or ''
                else:
                    message = do_op(*op) or ''
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception as e:
                message = str(e)
            do_pstack = True

        if do_pstack:
            pstack(message)
            do_pentry = True

        if do_pentry:
            impl.setline(5, ">>> " + "".join(entry) + "_")

        if do_pentry or do_pstack:
            impl.refresh()

loop()

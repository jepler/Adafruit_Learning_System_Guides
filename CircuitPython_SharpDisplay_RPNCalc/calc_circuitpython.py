import sys
import math
import time

import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
from adafruit_hid.keycode import Keycode
from adafruit_display_text.label import Label
import board
import displayio
import digitalio
import framebufferio
import sharpdisplay
import supervisor
import terminalio

from jepler_matrixkeypad import MatrixKeypad, LS1, LL0

col_pins = (board.A0, board.A1, board.A2, board.A3)
row_pins = (board.D0, board.D1, board.D2, board.D3, board.D4, board.D5)

BS = '\x7f'
CR = '\n'

ITM = ' .0254*'
FTM = ' .3048*'
MTI = ' .0254/'
FTM = ' .3048/'

LTF = ' 33.814023*'
FTL = ' 0.02957353*'

PTK = ' .45359237*'
KTP = ' 2.2046226*'

PI = ' %f' % math.pi
E = ' %f' % math.e

layers = (
    (
        ('^', 'l', 'r', LS1),
        ('s', 'c', 't', '/'),
        ('7', '8', '9', '*'),
        ('4', '5', '6', '-'),
        ('1', '2', '3', '+'),
        ('0', '.',  BS,  CR)
    ),

    (
        ('v', 'L', 'R', LL0),
        ('S', 'C', 'T', 'N'),
        (ITM, MTI,  PI, '^'),
        (LTF, FTL,   E, 'n'),
        (PTK, KTP, '3', '+'),
        ('=', '@',  BS, '~')
    ),
)


class Impl:
    def __init__(self):
        # Initialize the display, cleaning up after a display from the previous
        # run if necessary
        displayio.release_displays()
        framebuffer = sharpdisplay.SharpMemoryFramebuffer(board.SPI(),
                board.D10,
                400,
                240)
        self.display = framebufferio.FramebufferDisplay(framebuffer,
                auto_refresh=True)

        self.keypad = MatrixKeypad(row_pins, col_pins, layers)

        self.keyboard = Keyboard(usb_hid.devices)
        self.keyboard_layout = KeyboardLayoutUS(self.keyboard)

        g = displayio.Group(max_size=7)

        self.labels = labels = []
        labels.append(Label(terminalio.FONT, max_glyphs=32, scale=2, color=0))
        labels.append(Label(terminalio.FONT, max_glyphs=32, scale=3, color=0))
        labels.append(Label(terminalio.FONT, max_glyphs=32, scale=3, color=0))
        labels.append(Label(terminalio.FONT, max_glyphs=32, scale=3, color=0))
        labels.append(Label(terminalio.FONT, max_glyphs=32, scale=3, color=0))
        labels.append(Label(terminalio.FONT, max_glyphs=32, scale=3, color=0))

        y = 0
        for i, li in enumerate(labels):
            li.anchored_position = (1, max(1, 41 * i - 7))
            li.anchor_point = (0,0)
            g.append(li)

        bitmap = displayio.Bitmap((self.display.width + 126)//127, (self.display.height + 126)//127, 1)
        palette = displayio.Palette(1)
        palette[0] = 0xffffff

        tile_grid = displayio.TileGrid(bitmap, pixel_shader=palette)
        bg = displayio.Group(scale=127)
        bg.append(tile_grid)

        g.insert(0, bg)

        self.display.show(g)

        shifted = False

    def getch(self):
        while True:
            time.sleep(.002)
            c = self.keypad.getch()
            if c is not None:
                return c

            if supervisor.runtime.serial_bytes_available:
                return sys.stdin.read(1)

    def setline(self, i, text):
        li = self.labels[i]
        if text == li.text: return
        li.text = text
        li.anchored_position = (1, max(1, 41 * i - 7))
        li.anchor_point = (0,0)

    def refresh(self):
        pass

    def paste(self, text):
        text = str(text)
        self.keyboard_layout.write(text)

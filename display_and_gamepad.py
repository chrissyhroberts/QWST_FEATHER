# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import board
import terminalio
import displayio
from adafruit_display_text import label
import busio
import time
from adafruit_bus_device.i2c_device import I2CDevice
import struct

# ----- Configurable Constants -----
BORDER = 10

# ----- Fonts -----
FONT_BIG = 4
FONT_MEDIUM = 3
FONT_SMALL= 3

# ----- Basic Colors -----
BLACK       = 0x000000
WHITE       = 0xFFFFFF
RED         = 0xFF0000
GREEN       = 0x00FF00
BLUE        = 0x0000FF
YELLOW      = 0xFFFF00
CYAN        = 0x00FFFF
MAGENTA     = 0xFF00FF
GRAY        = 0x808080
LIGHT_GRAY  = 0xC0C0C0
DARK_GRAY   = 0x404040

# ----- Extended Colors -----
ORANGE      = 0xFFA500
GOLD        = 0xFFD700
SKY_BLUE    = 0x87CEEB
TEAL        = 0x008080
PINK        = 0xFFC0CB
PURPLE      = 0x800080
BROWN       = 0xA52A2A
FOREST_GREEN= 0x228B22
NAVY        = 0x000080
LIME_GREEN  = 0x32CD32
SALMON      = 0xFA8072
TURQUOISE   = 0x40E0D0
INDIGO      = 0x4B0082
MINT        = 0x98FF98
PEACH       = 0xFFE5B4
BEIGE       = 0xF5F5DC
TEXT_COLOR  = 0xFFFF00

# ----- Setup Display -----
display = board.DISPLAY

# ----- Display Drawing Functions -----
def make_background(color, width, height):
    bitmap = displayio.Bitmap(width, height, 1)
    palette = displayio.Palette(1)
    palette[0] = color
    return displayio.TileGrid(bitmap, pixel_shader=palette, x=0, y=0)

def make_inner_rect(color, width, height, border):
    inner_width = width - border * 2
    inner_height = height - border * 2
    bitmap = displayio.Bitmap(inner_width, inner_height, 1)
    palette = displayio.Palette(1)
    palette[0] = color
    return displayio.TileGrid(bitmap, pixel_shader=palette, x=border, y=border)

def make_text(text, color, font=terminalio.FONT, scale=1, position=(0, 0)):
    text_area = label.Label(font, text=text, color=color)
    text_group = displayio.Group(scale=scale, x=position[0], y=position[1])
    text_group.append(text_area)
    return text_group

def make_rect(x, y, width, height, color):
    bitmap = displayio.Bitmap(width, height, 1)
    palette = displayio.Palette(1)
    palette[0] = color
    return displayio.TileGrid(bitmap, pixel_shader=palette, x=x, y=y)

# ----- QWST Controller Functions -----
i2c = busio.I2C(board.SCL, board.SDA)
device = I2CDevice(i2c, 0x21)

INPUT_PORT0 = 0x00
OUTPUT_PORT0 = 0x02
LED_MAPPING = (0x6, 0x7, 0x9, 0xA)

BUTTON_MAPPING = {
    'A': 0xE, 'B': 0xC, 'X': 0xF, 'Y': 0xD,
    'U': 0x1, 'D': 0x4, 'L': 0x2, 'R': 0x3,
    '+': 0xB, '-': 0x5
}

BUTTON_TO_LED = {'L': 1, 'R': 2, 'Y': 3, 'A': 4}
led_state = 0b0000
last_button_state = 0

# ----- Display Group Setup -----
splash = displayio.Group()
splash.append(make_background(WHITE, display.width, display.height))
splash.append(make_inner_rect(GRAY, display.width, display.height, BORDER))
splash.append(make_text("Hello World!", PEACH, scale=FONT_MEDIUM, position=(10, 80)))
splash.append(make_rect(30, 60, 30, 60, RED))

# Create a text group for dynamic button press display
button_text_group = make_text("", BLACK, scale=FONT_SMALL, position=(10, 10))
splash.append(button_text_group)

display.root_group = splash

# ----- QWST Functions -----
def write_register_16bit(reg, value):
    buffer = struct.pack("<H", value)
    with device:
        device.write(bytearray([reg]) + buffer)

def read_register_16bit(reg):
    buffer = bytearray(2)
    with device:
        device.write_then_readinto(bytearray([reg]), buffer)
    return struct.unpack("<H", buffer)[0]

def read_buttons():
    return ~read_register_16bit(INPUT_PORT0) & 0xFFFF

def update_leds():
    output = 0
    for i in range(4):
        if (led_state >> i) & 1:
            output |= (1 << LED_MAPPING[i])
    write_register_16bit(OUTPUT_PORT0, output)

def toggle_led(led_num):
    global led_state
    if 1 <= led_num <= 4:
        led_state ^= (1 << (led_num - 1))
        update_leds()

def clear_leds():
    global led_state
    led_state = 0b0000
    update_leds()

def init_qwst():
    try:
        write_register_16bit(0x06, 0b11111001_00111111)
        write_register_16bit(0x05, 0b11111000_00111111)
        write_register_16bit(0x02, 0b00000110_11000000)
        print("QwSTPad initialized!")
    except OSError as e:
        print(f"Error initializing QwSTPad: {e}")

# ----- Init and Setup -----
init_qwst()
clear_leds()

# ----- Main Loop -----
while True:
    button_state = read_buttons()

    for button, bit_pos in BUTTON_MAPPING.items():
        if (button_state & (1 << bit_pos)) and not (last_button_state & (1 << bit_pos)):
            # Update the text inside the group (index 0 is the label)
            button_text_group[0].text = f"Pressed: {button}"
            if button in BUTTON_TO_LED:
                toggle_led(BUTTON_TO_LED[button])

    last_button_state = button_state
    time.sleep(0.1)

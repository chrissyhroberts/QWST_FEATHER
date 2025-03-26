# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import board
import terminalio
import displayio
from adafruit_display_text import label
import busio
import time
import rtc
import os
from adafruit_bus_device.i2c_device import I2CDevice
import struct

# ----- Configurable Constants -----
BORDER = 10
CSV_FILENAME = "/data_log.csv"

# ----- Font and Scale -----
FONT = terminalio.FONT
SCALE_BIG = 2
SCALE_MED = 1
SCALE_SMALL = 1

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
def make_text(text, color, font=None, scale=1, position=(0, 0)):
    if font is None:
        font = FONT
    text_area = label.Label(font, text=text, color=color)
    text_group = displayio.Group(scale=scale, x=position[0], y=position[1])
    text_group.append(text_area)
    return text_group

def make_rect(x, y, width, height, color):
    bitmap = displayio.Bitmap(width, height, 1)
    palette = displayio.Palette(1)
    palette[0] = color
    return displayio.TileGrid(bitmap, pixel_shader=palette, x=x, y=y)

def make_gradient(width, height, color_start, color_end):
    bitmap = displayio.Bitmap(width, height, height)
    palette = displayio.Palette(height)
    for y in range(height):
        ratio = y / height
        r = int(((color_end >> 16) & 0xFF) * ratio + ((color_start >> 16) & 0xFF) * (1 - ratio))
        g = int(((color_end >> 8) & 0xFF) * ratio + ((color_start >> 8) & 0xFF) * (1 - ratio))
        b = int((color_end & 0xFF) * ratio + (color_start & 0xFF) * (1 - ratio))
        palette[y] = (r << 16) | (g << 8) | b
        for x in range(width):
            bitmap[x, y] = y
    return displayio.TileGrid(bitmap, pixel_shader=palette, x=0, y=0)

def get_score_color(score, min_score, max_score):
    ratio = (score - min_score) / (max_score - min_score)
    red = int(255 * (1 - ratio))
    green = int(255 * ratio)
    return (red << 16) | (green << 8)

# ----- Emoji Helper -----
def get_emoji(score, min_score, max_score):
    ratio = (score - min_score) / (max_score - min_score)
    if ratio <= 0.2:
        return "😞"
    elif ratio <= 0.4:
        return "🙁"
    elif ratio <= 0.6:
        return "😐"
    elif ratio <= 0.8:
        return "🙂"
    else:
        return "😄"

# ----- Welcome Screen -----
def show_welcome(text="Welcome! Press A to begin"):
    splash = displayio.Group()
    splash.append(make_gradient(display.width, display.height, NAVY, SKY_BLUE))
    welcome_label = make_text(text, WHITE, font=FONT, scale=SCALE_MED,
                              position=(20, display.height // 2 - 10))
    splash.append(welcome_label)
    display.root_group = splash

    global last_button_state
    while True:
        button_state = read_buttons()
        if (button_state & (1 << BUTTON_MAPPING['A'])) and not (last_button_state & (1 << BUTTON_MAPPING['A'])):
            last_button_state = button_state
            return
        last_button_state = button_state
        time.sleep(0.1)

# ----- Transition Screen -----
def show_transition():
    splash = displayio.Group()
    splash.append(make_gradient(display.width, display.height, DARK_GRAY, BLACK))
    wait_label = make_text("Next...", WHITE, font=FONT, scale=SCALE_MED,
                           position=(display.width // 2 - 20, display.height // 2 - 5))
    splash.append(wait_label)
    display.root_group = splash
    time.sleep(0.5)

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

led_state = 0b0000
last_button_state = 0

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

def toggle_led_by_index(led_num):
    global led_state
    if 1 <= led_num <= 4:
        led_state ^= (1 << (led_num - 1))
        update_leds()

def toggle_all_leds():
    global led_state
    led_state ^= 0b1111
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

# ----- Question Flow -----
def question(variable_name, min_score, max_score, variable_code=None, use_emoji=False):
    try:
        try:
            os.stat(CSV_FILENAME)
        except OSError:
            with open(CSV_FILENAME, "w") as f:
                f.write("timestamp,variable,score\n")
    except OSError as e:
        print(f"⚠️ Cannot access filesystem: {e}")

    splash = displayio.Group()
    splash.append(make_gradient(display.width, display.height, SKY_BLUE, WHITE))
    display.root_group = splash

    widget = displayio.Group()

    title = make_text(variable_name, DARK_GRAY, font=FONT, scale=SCALE_BIG, position=(20, 20))
    widget.append(title)

    box_x = 20
    box_y = 70
    box_width = display.width - 40
    box_height = 30
    outline = make_rect(box_x, box_y, box_width, box_height, DARK_GRAY)
    widget.append(outline)

    fill_bitmap = displayio.Bitmap(box_width, box_height, 1)
    fill_palette = displayio.Palette(1)
    fill_palette[0] = RED
    fill = displayio.TileGrid(fill_bitmap, pixel_shader=fill_palette, x=box_x, y=box_y)
    widget.append(fill)

    score_label = make_text("0", BLACK, font=FONT, scale=SCALE_MED,
                            position=(box_x + box_width // 2 - 8, box_y + box_height // 2 - 6))
    widget.append(score_label)

    if use_emoji:
        emoji_label = make_text(get_emoji(min_score, min_score, max_score), BLACK, font=FONT, scale=SCALE_MED,
                                position=(box_x + box_width + 10, box_y))
        widget.append(emoji_label)
    else:
        emoji_label = None

    splash.append(widget)

    score = min_score
    global last_button_state
    debounce_time = 0.2

    while True:
        button_state = read_buttons()

        for button, bit_pos in BUTTON_MAPPING.items():
            if (button_state & (1 << bit_pos)) and not (last_button_state & (1 << bit_pos)):

                if button == 'R' and score < max_score:
                    score += 1
                elif button == 'L' and score > min_score:
                    score -= 1
                elif button == 'A':
                    now = time.localtime()
                    timestamp = str(time.mktime(now))
                    try:
                        code = variable_code if variable_code else variable_name
                        with open(CSV_FILENAME, "a") as f:
                            f.write(f"{timestamp},{code},{score}\n")
                        last_button_state = button_state
                        return
                    except OSError as e:
                        print(f"⚠️ Could not write to file: {e}")
                        last_button_state = button_state
                        return

                score_label[0].text = str(score)
                bar_width = int(((score - min_score) / (max_score - min_score)) * fill_bitmap.width)
                for x in range(fill_bitmap.width):
                    for y in range(fill_bitmap.height):
                        fill_bitmap[x, y] = 1 if x < bar_width else 0
                fill_palette[0] = get_score_color(score, min_score, max_score)
                if emoji_label:
                    emoji_label[0].text = get_emoji(score, min_score, max_score)

        last_button_state = button_state
        time.sleep(debounce_time)

# ----- Init and Run Loop -----
init_qwst()
clear_leds()
show_welcome("Press A to begin rating")

while True:
    question("comfort", 0, 3, "c", use_emoji=False)
    show_transition()
    question("clarity", 0, 5, "l", use_emoji=True)
    show_transition()
    question("confidence", 0, 10, "f", use_emoji=False)
    show_transition()

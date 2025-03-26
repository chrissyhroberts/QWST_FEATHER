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

# ----- Data Entry Widget -----
def create_score_widget(label_text):
    widget_group = displayio.Group()

    title = make_text(label_text, BLACK, scale=FONT_MEDIUM, position=(10, 10))
    widget_group.append(title)

    box_x = 10
    box_y = 40
    box_width = display.width - 20
    box_height = 20
    outline = make_rect(box_x, box_y, box_width, box_height, BLACK)
    widget_group.append(outline)

    fill_bitmap = displayio.Bitmap(box_width, box_height, 1)
    fill_palette = displayio.Palette(1)
    fill_palette[0] = RED
    fill = displayio.TileGrid(fill_bitmap, pixel_shader=fill_palette, x=box_x, y=box_y)
    widget_group.append(fill)

    score_label = make_text("0", BLACK, scale=FONT_MEDIUM, position=(box_x + box_width + 5, box_y - 5))
    widget_group.append(score_label)

    return widget_group, fill, fill_bitmap, score_label

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

# ----- Question Flow Function -----
def question(variable_name, min_score, max_score, variable_code=None):
    # Ensure the CSV file exists with headers
    try:
        try:
            os.stat(CSV_FILENAME)
            print("CSV file already exists.")
        except OSError:
            print("Creating CSV file with header...")
            with open(CSV_FILENAME, "w") as f:
                print("Writing header to new CSV file")
                f.write("timestamp,variable,score\n")
    except OSError as e:
        print(f"⚠️ Cannot access filesystem: {e}")

    splash = displayio.Group()
    splash.append(make_background(WHITE, display.width, display.height))
    display.root_group = splash

    widget, fill, fill_bitmap, score_label = create_score_widget(variable_name)
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
                        print(f"Saving to CSV: {timestamp},{code},{score}")
                        with open(CSV_FILENAME, "a") as f:
                            f.write(f"{timestamp},{code},{score}\n")
                            print("Write successful")
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

        last_button_state = button_state
        time.sleep(debounce_time)

# ----- Init and Run Loop -----
init_qwst()
clear_leds()

while True:
    question("comfort", 0, 3, "c")
    question("clarity", 0, 5, "l")
    question("confidence", 0, 10, "f")

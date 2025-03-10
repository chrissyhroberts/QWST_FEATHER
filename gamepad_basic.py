import board
import busio
import time
from adafruit_bus_device.i2c_device import I2CDevice
import struct

# Initialize I2C
i2c = busio.I2C(board.SCL, board.SDA)
device = I2CDevice(i2c, 0x21)  # Mini QWST is at 0x21

# Mini QWST Constants
INPUT_PORT0 = 0x00  
OUTPUT_PORT0 = 0x02  # LED control register
LED_MAPPING = (0x6, 0x7, 0x9, 0xA)  # LED bit positions

# Button mapping (from QwSTPad library)
BUTTON_MAPPING = {
    'A': 0xE, 'B': 0xC, 'X': 0xF, 'Y': 0xD,
    'U': 0x1, 'D': 0x4, 'L': 0x2, 'R': 0x3,
    '+': 0xB, '-': 0x5
}

BUTTON_TO_LED = {'A': 1, 'B': 2, 'X': 3, 'Y': 4}  # Assign buttons to LEDs

# LED state tracking
led_state = 0b0000  
last_button_state = 0  # Store previous button states

def write_register_16bit(reg, value):
    """Write a 16-bit value to an I2C register."""
    buffer = struct.pack("<H", value)
    with device:
        device.write(bytearray([reg]) + buffer)

def read_register_16bit(reg):
    """Read a 16-bit value from an I2C register."""
    buffer = bytearray(2)
    with device:
        device.write_then_readinto(bytearray([reg]), buffer)
    return struct.unpack("<H", buffer)[0]  # Convert to integer

def read_buttons():
    """Read button states, correct for active-low logic."""
    button_state = read_register_16bit(INPUT_PORT0)
    return ~button_state & 0xFFFF  # Invert active-low logic

def update_leds():
    """Update the LED states based on led_state bitmask."""
    output = 0
    for i in range(4):
        output |= (1 << LED_MAPPING[i]) if ((led_state >> i) & 1) else output
    write_register_16bit(OUTPUT_PORT0, output)

def toggle_led(led_num):
    """Toggle a specific LED on/off."""
    global led_state
    if 1 <= led_num <= 4:
        led_state ^= (1 << (led_num - 1))  # Toggle bit
        update_leds()

def clear_leds():
    """Turn off all LEDs."""
    global led_state
    led_state = 0b0000
    update_leds()

def init_qwst():
    """Initialize Mini QWST by setting up registers."""
    try:
        write_register_16bit(0x06, 0b11111001_00111111)  # Config
        write_register_16bit(0x05, 0b11111000_00111111)  # Polarity
        write_register_16bit(0x02, 0b00000110_11000000)  # Output
        print("QwSTPad initialized!")
    except OSError as e:
        print(f"Error initializing QwSTPad: {e}")

# Initialize the device
init_qwst()
clear_leds()

print("Press buttons to toggle LEDs...")

# Main loop: Toggle LEDs based on button presses
while True:
    button_state = read_buttons()

    for button, bit_pos in BUTTON_MAPPING.items():
        # Detect button press only when transitioning from unpressed -> pressed
        if (button_state & (1 << bit_pos)) and not (last_button_state & (1 << bit_pos)):
            if button in BUTTON_TO_LED:
                toggle_led(BUTTON_TO_LED[button])  # Toggle the assigned LED
    
    last_button_state = button_state  # Store current state for debounce
    time.sleep(0.1)  # Small delay to prevent spamming

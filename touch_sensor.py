import board
import touchio
import time
import displayio
from adafruit_display_text import label
import terminalio

# Constants
TOUCH_THRESHOLD = 16000  # Adjust if needed based on your earlier test

# Set up display
display = board.DISPLAY
main_group = displayio.Group()
display.root_group = main_group

# Set up touch sensor
touch = touchio.TouchIn(board.A4)

# Set up text elements
value_label = label.Label(terminalio.FONT, text="Touch value: ----", color=0xFFFF00, x=10, y=20)
status_label = label.Label(terminalio.FONT, text="Status: ???", color=0x00FFFF, x=10, y=50)
main_group.append(value_label)
main_group.append(status_label)

# Create a basic bar background
BAR_X = 10
BAR_Y = 80
BAR_WIDTH = 200
BAR_HEIGHT = 20

bar_outline = displayio.Bitmap(BAR_WIDTH, BAR_HEIGHT, 1)
bar_palette = displayio.Palette(1)
bar_palette[0] = 0xFFFFFF
bar_frame = displayio.TileGrid(bar_outline, pixel_shader=bar_palette, x=BAR_X, y=BAR_Y)
main_group.append(bar_frame)

# Fill area (we will update this)
bar_fill_bitmap = displayio.Bitmap(BAR_WIDTH, BAR_HEIGHT, 1)
bar_fill_palette = displayio.Palette(1)
bar_fill_palette[0] = 0x00FF00  # Green
bar_fill = displayio.TileGrid(bar_fill_bitmap, pixel_shader=bar_fill_palette, x=BAR_X, y=BAR_Y)
main_group.append(bar_fill)

while True:
    raw = touch.raw_value
    touched = raw > TOUCH_THRESHOLD

    # Update labels
    value_label.text = f"Touch value: {raw}"
    status_label.text = "Status: TOUCH DETECTED" if touched else "Status: no touch"

    # Update bar graph
    fill_width = int((raw - 10000) / 10000 * BAR_WIDTH)  # Normalized for 10k–20k range
    fill_width = min(max(fill_width, 0), BAR_WIDTH)

    for x in range(BAR_WIDTH):
        for y in range(BAR_HEIGHT):
            bar_fill_bitmap[x, y] = 1 if x < fill_width else 0

    time.sleep(0.1)

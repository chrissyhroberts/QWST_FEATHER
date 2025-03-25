import board
import touchio
import storage
import usb_cdc
import digitalio
import time

# Touch setup (A4 in your case)
touch = touchio.TouchIn(board.A4)
TOUCH_THRESHOLD = 17000  # You can fine-tune this

# LED for feedback (onboard)
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

def blink(n):
    for _ in range(n):
        led.value = True
        time.sleep(0.15)
        led.value = False
        time.sleep(0.15)

# Check raw touch value
if touch.raw_value < TOUCH_THRESHOLD:
    # Touched: enable CIRCUITPY (host access mode)
    storage.enable_usb_drive()
    usb_cdc.enable(console=True, data=False)
    blink(1)  # 🔓 1 blink = USB mode
else:
    # Not touched: disable USB so device can write logs
    storage.disable_usb_drive()
    usb_cdc.enable(console=True, data=False)
    blink(2)  # ✏️ 2 blinks = Logging mode

# QWST_FEATHER

## Adafruit-ESP32-S3-TFT-Feather-PCB

* Main Repo for board - https://github.com/adafruit/Adafruit-ESP32-S3-TFT-Feather-PCB
* Knowledge base for board here - https://learn.adafruit.com/adafruit-esp32-s3-tft-feather/
* Factory reset board using browswer based esptool - https://adafruit.github.io/Adafruit_WebSerial_ESPTool/
	* Instructions here - https://learn.adafruit.com/adafruit-esp32-s3-tft-feather/factory-reset#factory-reset-and-bootloader-repair-3107941
* Good version of circuitpython here https://circuitpython.org/board/adafruit_feather_esp32s3_tft/

## adalogger-featherwing-rtc-sd-add-on-for-all-feather-boards

https://shop.pimoroni.com/products/adalogger-featherwing-rtc-sd-add-on-for-all-feather-boards?variant=16853702663


## Flash

Get a list of devices

`ls /dev/cu.usb*`

Erase the drive

`esptool.py --port /dev/cu.usbmodem2101 erase_flash`

Add back the new firmware

`esptool.py --port /dev/cu.usbmodem2101 write_flash -z 0x0 adafruit-circuitpython-adafruit_feather_esp32s3_tft-en_GB-9.2.6.bin`

## boot.py

Needs to make file system writeable

```import storage

# Force remount of internal filesystem as writable
storage.remount("/", readonly=False)```


## TO DO

🔘 1. Binary Choice (Yes/No, True/False)
Two big buttons or icons (✓ and ✗, thumbs up/down)
Selection box toggles between them
A shows selection
🧠 Good for: consent questions, Boolean fields.

🎯 2. Target Slider / Dial
Horizontal dial or arc with a pointer that rotates or slides
Visually resembles a thermostat or volume knob
Use L/R to rotate, A to confirm
🧠 Good for: intuitive range feedback (e.g., "How warm do you feel?").

🌈 3. Color Picker
Display colored swatches (e.g., red, yellow, green, blue, purple)
Move selection box left/right to choose a color
A confirms
🧠 Good for: mood tracking, qualitative impressions.

🟦 4. Grid Selector (2D Positioning)
3×3 grid (or 4×4) where user navigates with U/D/L/R
A selects
Label rows/columns (e.g., "importance" vs "urgency")
🧠 Good for: matrix-style questions, categorization tasks.

🔢 5. Number Pad Entry
Mimic a calculator keypad (3×3 + enter)
Display current number at top
Use A to enter, B to clear, arrows to navigate
🧠 Good for: entering exact values (age, weight, count).

📈 6. Trend Indicator
Show three icons: ⬆️ (better), ➡️ (same), ⬇️ (worse)
Choose which best describes change since last time
🧠 Good for: measuring improvement or decline over time.

🎨 7. Custom Icon Sets
Replace faces with other meaningful symbols: food portions, pain scales, activity levels, etc.
🧠 Great for thematic surveys.

Would you like me to start building one of these out? I’d suggest the grid selector or binary choice next since they visually complement what you’ve already built.
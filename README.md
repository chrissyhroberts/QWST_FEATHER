# QWST_FEATHER

## Factory reset board at https://learn.adafruit.com/adafruit-esp32-s3-tft-feather/factory-reset#factory-reset-and-bootloader-repair-3107941

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
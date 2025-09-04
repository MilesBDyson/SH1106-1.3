#!/usr/bin/env python3
# sh1106_i2c.py - Simple SH1106 I2C example for 128x64 display at 0x3C on bus 1
# Requires: pip install smbus2 Pillow

from smbus2 import SMBus
from PIL import Image, ImageDraw, ImageFont
import time
import bme280_sensor


I2C_BUS = 2
I2C_ADDR = 0x3C  # SH1106 default (commonly)
WIDTH = 132      # SH1106 internal width (driver column count)
VISIBLE_WIDTH = 128
HEIGHT = 64
PAGES = HEIGHT // 8

# Control bytes
CMD = 0x00
DATA = 0x40

# Basic init sequence for SH1106 (128x64) — tuned for many modules
INIT_SEQ = [
    (CMD, 0xAE),             # DISPLAY OFF
    (CMD, 0xD5), (CMD, 0x80), # SET DISPLAY CLOCK DIV
    (CMD, 0xA8), (CMD, 0x3F), # SET MULTIPLEX (0x3F = 63)
    (CMD, 0xD3), (CMD, 0x00), # SET DISPLAY OFFSET
    (CMD, 0x40),             # SET START LINE = 0
    (CMD, 0xAD), (CMD, 0x8B), # SET DC-DC ON (charge pump) - many SH1106 modules use external DC/DC; try 0x8B or 0x8A
    (CMD, 0xA1),             # SEGMENT REMAP (column addr remap)
    (CMD, 0xC8),             # COM SCAN DEC (remap)
    (CMD, 0xDA), (CMD, 0x12), # SET COM PINS
    (CMD, 0x81), (CMD, 0x7F), # SET CONTRAST
    (CMD, 0xD9), (CMD, 0x22), # SET PRE-CHARGE
    (CMD, 0xDB), (CMD, 0x40), # SET VCOM DETECT
    (CMD, 0xA4),             # DISPLAY ALL ON RESUME
    (CMD, 0xA6),             # NORMAL DISPLAY (A7 = inverse)
    (CMD, 0xAF)              # DISPLAY ON
]

class SH1106:
    def __init__(self, bus=I2C_BUS, addr=I2C_ADDR):
        self.bus_num = bus
        self.addr = addr
        self.bus = SMBus(self.bus_num)
        # Initialize display
        for btype, val in INIT_SEQ:
            self._write_cmd(val)
        # buffer: visible width x height (128x64) stored in pages (8 rows per page)
        self.buffer = bytearray(VISIBLE_WIDTH * PAGES)

    def _write_cmd(self, byte):
        # control byte 0x00 before command
        self.bus.write_byte_data(self.addr, CMD, byte)

    def _write_data(self, data):
        # write in chunks (I2C has size limits)
        chunk_size = 32
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i+chunk_size]
            # send control byte 0x40 then data bytes
            self.bus.write_i2c_block_data(self.addr, DATA, list(chunk))

    def show(self):
        # SH1106 expects 132 columns internally; many displays map visible 128 columns starting at offset 2
        col_offset = 2
        for page in range(PAGES):
            # Set page address (0xB0 + page)
            self._write_cmd(0xB0 + page)
            # Set lower column start address
            self._write_cmd(0x00 + (col_offset & 0x0F))
            # Set higher column start address
            self._write_cmd(0x10 + ((col_offset >> 4) & 0x0F))
            # Extract 128 bytes for this page from buffer
            start = page * VISIBLE_WIDTH
            end = start + VISIBLE_WIDTH
            page_bytes = self.buffer[start:end]
            self._write_data(page_bytes)

    def clear(self):
        for i in range(len(self.buffer)):
            self.buffer[i] = 0x00

    def pixel(self, x, y, color=1):
        if not (0 <= x < VISIBLE_WIDTH and 0 <= y < HEIGHT): 
            return
        page = y // 8
        idx = x + page * VISIBLE_WIDTH
        bit = 1 << (y & 7)
        if color:
            self.buffer[idx] |= bit
        else:
            self.buffer[idx] &= ~bit

    def image(self, pil_img):
        # Expects a PIL Image in mode '1' sized 128x64
        if pil_img.mode != '1':
            pil_img = pil_img.convert('1')
        img = pil_img.crop((0, 0, VISIBLE_WIDTH, HEIGHT)).convert('1')
        pix = img.load()
        # Convert to page buffer (LSB = top)
        for y in range(HEIGHT):
            for x in range(VISIBLE_WIDTH):
                if pix[x, y] == 255:
                    self.pixel(x, y, 1)
                else:
                    self.pixel(x, y, 0)

    def close(self):
        self.bus.close()
def main():
    oled = SH1106()
    oled.clear()

    # Create an image with Pillow
    img = Image.new('1', (VISIBLE_WIDTH, HEIGHT), 0)  # 0=black background
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 15)
    except:
        font = ImageFont.load_default()
    oled.clear()
    while True:
        draw = ImageDraw.Draw(img)
        draw.rectangle((0, 18, 128, 64), outline=0, fill=0)
        text = "Hello World"
        draw.text((1, 10), text, font=font, fill=255)
        oled.image(img)
        oled.show()
        time.sleep(5)

if __name__ == '__main__':
  try:
    main()
  except KeyboardInterrupt:
    pass
  finally:
    oled = SH1106()
    oled.clear()
    oled.show()















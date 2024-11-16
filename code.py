import board
import busio
import terminalio
import displayio
from adafruit_display_text.label import Label
import adafruit_ili9341
import digitalio
import time
import vectorio

tft_cs = board.A3
tft_reset = board.A2
tft_dc = board.A1
touch_cs = digitalio.DigitalInOut(board.A0)

button = digitalio.DigitalInOut(board.D0) # boot button
button.pull = digitalio.Pull.UP

spi = board.SPI()

def outer_loop():
    print("Begin.")

    # Release any resources currently in use for the displays
    displayio.release_displays()

    display_bus = displayio.FourWire(
        spi, command=tft_dc, chip_select=tft_cs, reset=tft_reset)

    touch_cs.direction = digitalio.Direction.OUTPUT
    touch_cs.value = True

    display = adafruit_ili9341.ILI9341(display_bus, width=320, height=240)

    group = displayio.Group()
    display.show(group)

    palette = displayio.Palette(1)
    palette[0] = 0xffffff
    rectangle_h = vectorio.Rectangle(pixel_shader=palette, width=320, height=1, x=0, y=0)
    rectangle_v = vectorio.Rectangle(pixel_shader=palette, width=1, height=240, x=0, y=0)
    group.append(rectangle_h)
    group.append(rectangle_v)

    coords_label = Label(
        font=terminalio.FONT,
        text="xyz",
        color=0xffffff,
    )
    coords_label.anchor_point = (0.0, 0.0)
    coords_label.anchored_position = (0, 0)
    group.append(coords_label)

    # Loop until "boot" button is pressed.  If you connect a new display, just press the boot button
    # and the program will restart and reinitialize the display.
    while button.value:
        def get_val(cmd):
            tx_buf = bytearray(3)
            rx_buf = bytearray(3)
            tx_buf[0] = cmd
            while not spi.try_lock():
                pass
            spi.configure(baudrate=1000000, phase=0, polarity=0)
            touch_cs.value = False
            spi.write_readinto(tx_buf, rx_buf)
            touch_cs.value = True
            spi.unlock()
            return (rx_buf[1] << 4) | (rx_buf[2] >> 4)

        xraw  = get_val(0b10010000)
        yraw  = get_val(0b11010000)
        z1raw = get_val(0b10110000)
        z2raw = get_val(0b11000000)
        text = "%03x %03x %03x %03x" % (xraw, yraw, z1raw, z2raw)
        coords_label.text = text
        print(text)
        x = 320 - int(xraw * 320 / 0x800)
        y = 240 - int(yraw * 240 / 0x800)
        if x >= 0 and y >= 0 and x < 320 and y < 240:
            rectangle_v.x = x
            rectangle_h.y = y

while True:
    outer_loop()

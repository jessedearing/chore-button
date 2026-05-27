import datetime
from zoneinfo import ZoneInfo
import sqlite3
import RPi.GPIO as GPIO
from escpos.printer import Usb
import textwrap
from time import sleep, time


def get_chores():
    today = datetime.datetime.now(ZoneInfo("America/Los_Angeles")).date()
    with sqlite3.connect("chores.db") as db:
        rows = db.execute(
            "SELECT name FROM chores WHERE date = ? AND done = 0 ORDER BY id",
            (today,),
        ).fetchall()
    return [row[0] for row in rows]


PRINTER_VENDOR_ID = 0x1FC9
PRINTER_PRODUCT_ID = 0x2016
PRINTER_WIDTH = 48


def print_chores():
    printer = Usb(PRINTER_VENDOR_ID, PRINTER_PRODUCT_ID)
    try:
        printer.set(align="center", bold=False, width=1, height=1)
        printer.text("Chore List\n")

        printer.set(align="center", bold=False)
        printer.text(datetime.date.today().strftime("%A, %b %d %Y") + "\n")

        printer.text("-" * PRINTER_WIDTH + "\n")

        printer.set(align="left")
        chores = get_chores()
        for chore in chores:
            wrapped = textwrap.wrap(
                chore,
                width=PRINTER_WIDTH,
                initial_indent="[ ] ",
                subsequent_indent="    ",
            )
            printer.text("\n".join(wrapped) + "\n")

        printer.set(align="center")
        printer.text("-" * PRINTER_WIDTH + "\n")
        printer.text("\n\n\n\n")
        printer.cut()
    finally:
        printer.close()


def main():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(8, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    last_state = False
    last_press_time = 0.0

    while True:
        inp = GPIO.input(8)
        if inp and not last_state and (time() - last_press_time) >= 2:
            last_press_time = time()
            print_chores()

        last_state = inp
        sleep(0.15)

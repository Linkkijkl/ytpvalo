#!/usr/bin/env python
# -*- coding: utf-8 -*-

from dmxpy import DmxPy
import time
import sys
from serial.serialutil import SerialException
import argparse
from blessed import Terminal

import generators
import ui

DEFAULT_SERIAL_DEVICE = "/dev/ttyUSB0" # COMx in Windows
DEFAULT_TOTAL_LIGHTS = 50
DEFAULT_START_ADDRESS = 0
MIN_FRAME_TIME = 1/60
MAIN_GENERATOR = generators.metallic_noise

available_generators = {"metallic_noise": generators.metallic_noise,
                        "ytp": generators.ytp,
                        "color_noise": generators.color_noise,
                        "white": generators.white,
                        "blue": generators.blue,
                        "red": generators.red,
                        "green": generators.green,
                        "black": generators.black,
                        "rainbow": generators.rainbow}


def main():
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--serial-device", dest="serial_device", default=DEFAULT_SERIAL_DEVICE)
    parser.add_argument("-n", "--total-lights", dest="total_lights", default=DEFAULT_TOTAL_LIGHTS, type=int)
    parser.add_argument("-a", "--start-address", dest="start_address", default=DEFAULT_START_ADDRESS, type=int)
    parser.add_argument("-q", "--quiet", dest="quiet", action="store_true")
    parser.add_argument("-d", "--dry-run", dest="dry_run", action="store_true")
    args = parser.parse_args()

    current_generator = MAIN_GENERATOR

    # Initialize DMX
    dmx = None
    if not args.dry_run:
        try:
            dmx = DmxPy.DmxPy(serial_port=args.serial_device, dmx_size=args.start_address + args.total_lights * 3)
        except:
            exit(0)

    # Initialize GUI and register commands for it
    gui = ui.Gui()
    gui.register_command("exit", lambda *_: exit(0))

    def change_generator(new_generator: str):
        if not new_generator in available_generators.keys():
            return "Available generators: " + " ".join(available_generators.keys())
        nonlocal current_generator
        current_generator = available_generators[new_generator]
    gui.register_command("load", change_generator)

    start_time = time.perf_counter()

    while True:
        elapsed = time.perf_counter() - start_time

        # Render colors to DMX buffer and GUI
        for n in range(args.total_lights):
            color = current_generator(elapsed, n, args.total_lights)
            if not color: continue
            scaled_color = map(lambda a: int(min(max(a, 0.0), 1.0) * 255), color)
            for m in range(3):
                if not args.dry_run:
                    dmx.set_channel(n * 3 + m + args.start_address, scaled_color[m])
            if not args.quiet:
                gui.colors.append(scaled_color)

        # Draw DMX buffer
        if not args.dry_run:
            try:
                dmx.render()
            except SerialException:
                if not args.quiet:
                    gui.log_error("Serial write error")
                else:
                    sys.stderr.write("Serial write error")

        # Calculate frame time to show on GUI
        frame_start_time = elapsed + start_time
        frame_time = time.perf_counter() - frame_start_time
        gui.set_frame_time(frame_time)

        # Render GUI
        if not args.quiet:
            gui.render()

        # Wait to fulfill minimum frame time
        if frame_time < MIN_FRAME_TIME:
            sleep_for = MIN_FRAME_TIME - frame_time
            if not args.quiet:
                gui.poll(sleep_for)
            else:
                time.sleep(MIN_FRAME_TIME - frame_time)


if __name__ == "__main__":
    try:
        main()
    except(KeyboardInterrupt):
        exit(0)
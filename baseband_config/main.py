"""
This example demonstrates how to use an FTDI FT232H USB cable
to communicate with the Baseband. See the README.md file for
more information.

(C) 2024 PE1OBW, PE1MUD
"""
import argparse
import json
import msvcrt
import time
from baseband.baseband import Baseband
from baseband.settings import SETTINGS
from baseband.usb_easymcp import UsbEasyMcp
from baseband.usb_ftdi import UsbFtdi
from baseband.usb_mcp2221 import UsbMcp2221


GPIO_PULSE_LENGTH = 3  # Pulse length in seconds


def main():
    # Create an argument parser
    parser = argparse.ArgumentParser(description='Baseband Configuration Utility')

    # USB driver selection
    parser.add_argument('--usb_ftdi', action='store_true', help='Use FTDI USB to I2C bridge (=default)')
    parser.add_argument('--usb_mcp2221', action='store_true', help='Use MCP2221A USB to I2C bridge with MCP2221A library')
    parser.add_argument('--usb_easymcp', action='store_true', help='Use MCP2221A USB to I2C bridge with EasyMCP2221 library')

    # FT232H specific arguments
    parser.add_argument('--serial', type=str, help='Serial number of the FTDI device')
    parser.add_argument('--description', type=str, help='Description of the FTDI device')

    # Baseband commands
    parser.add_argument('--info', action='store_true', help='Read device info')
    parser.add_argument('--set', type=str, help='Set a setting (e.g. --set video.video_mode=PAL')
    parser.add_argument('--settings_to_file', type=str, help='Store actual settings to file')
    parser.add_argument('--settings_from_file', type=str, help='Read settings from file and write to baseband')
    parser.add_argument('--dump_osd', action='store_true', help='Dump OSD memory')
    parser.add_argument('--upgrade', type=str, help='Upgrade baseband firmware')
    parser.add_argument('--download_firmware', type=str, help='Download firmware from baseband')
    parser.add_argument('--pulse_gpio', type=int, help=f'Pulse GPIO pin <n> for {GPIO_PULSE_LENGTH} seconds')
    parser.add_argument('--read_meters', action='store_true', help='Show VU meter')
    parser.add_argument('--reboot', action='store_true', help='Reboot baseband')
    parser.add_argument('--load_preset', type=int, help='Load preset <n> (1..31)')
    parser.add_argument('--store_preset', type=int, help='Store actual settings to preset <n> (1..31)')
    parser.add_argument('--erase_preset', type=int, help='Erase preset <n> (1..31)')
    parser.add_argument('--show_presets', action='store_true', help='Show all used presets')
    args = parser.parse_args()

    if args.usb_mcp2221:
        usb_driver = UsbMcp2221()
    elif args.usb_easymcp:
        usb_driver = UsbEasyMcp()
    else:
        usb_driver = UsbFtdi(serial=args.serial, description=args.description)
    bb = Baseband(usb_driver)

    if args.pulse_gpio is not None:
        bb.pulse_gpio(args.pulse_gpio, GPIO_PULSE_LENGTH)
        return 0  # If pulse gpio is requested, do not do anything else (the baseband will be rebooted)

    # Read device info
    info = bb.get_info()
    print('Baseband succesfully connected. Info:')
    print(f'Hardware version:   {info["hw_version"]}\n'
          f'FPGA version:       {info["fpga_version"]}\n'
          f'Software version:   {info["sw_version"]}{" (bootloader, no image!)" if info["sw_version"] == "0.0" else ""}')

    if args.info:
        print('\nActual settings:')
        settings = bb.read_settings()
        bb.dump_settings(settings)
        print('\nPreset status:')
        preset_flags = bb.load_preset_status()
        for i, flag in enumerate(preset_flags):
            if i == 0:
                continue
            print(f'Preset {i:2}: {bb.get_preset(i).name.decode() if flag else "Empty":14}', end='' if i % 4 else '\n')

    if args.read_meters:
        while True:
            actuals = bb.read_actuals()
            print('Actuals:')
            for field in actuals._fields_:
                field_name = field[0]
                print(f'{field_name} = {getattr(actuals, field_name)}')
            time.sleep(1)
            if msvcrt.kbhit():
                break

    if args.settings_to_file:
        settings = bb.read_settings()
        bb.dump_settings(settings)
        with open(args.settings_to_file, 'w') as file:
            json.dump(bb.serialize(settings), file, indent=4)
        print(f'Settings read from baseband and written to {args.settings_to_file}')

    if args.settings_from_file:
        with open(args.settings_from_file, 'r') as file:
            current_settings = bb.read_settings()
            serialized_settings = json.load(file)
            settings = bb.deserialize(serialized_settings, SETTINGS, current_settings)
            bb.write_settings(settings)
            bb.dump_settings(settings)
        print(f'Settings read from {args.settings_from_file} and written to baseband')

    if args.dump_osd:
        bb.dump_osd_memory()

    if args.upgrade:
        with open(args.upgrade, 'rb') as file:
            firmware_data = file.read()
        bb.flash_firmware(firmware_data)
    if args.download_firmware:
        assert args.usb_easymcp, 'Firmware download is only supported with EasyMCP2221'
        firmware_data = bb.read_firmware()
        with open(args.download_firmware, 'wb') as file:
            file.write(firmware_data)
        print(f'Firmware downloaded to {args.download_firmware}')

    if args.reboot:
        bb.reboot()

    if args.show_presets:
        preset_flags = bb.load_preset_status()
        for i, flag in enumerate(preset_flags):
            if i == 0:
                continue
            print(f'Preset {i}: {"" if flag else "Empty"}')
            if flag:
                bb.dump_settings(bb.get_preset(i))
                print()

    if args.load_preset:
        bb.load_preset(args.load_preset)
        print(f'Preset {args.load_preset} loaded:')
        bb.dump_settings(bb.read_settings())

    if args.store_preset:
        settings = bb.read_settings()
        bb.write_settings(settings)
        bb.store_preset(args.store_preset)
        print(f'Actual settings stored to preset {args.store_preset}')

    if args.erase_preset:
        bb.erase_preset(args.erase_preset)
        print(f'Preset {args.erase_preset} erased')

    if args.set:
        setting, value = args.set.split('=')
        bb.set_setting(setting, value)

if __name__ == '__main__':
    main()

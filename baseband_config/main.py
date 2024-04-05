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


def main():
    # Create an argument parser
    parser = argparse.ArgumentParser(description='Baseband Configuration Utility')
    parser.add_argument('--serial', type=str, help='Serial number of the FTDI device')
    parser.add_argument('--description', type=str, help='Description of the FTDI device')
    parser.add_argument('--info', action='store_true', help='Read device info')
    parser.add_argument('--settings_to_file', type=str, help='Store actual settings to file')
    parser.add_argument('--settings_from_file', type=str, help='Read settings from file and write to baseband')
    parser.add_argument('--dump_osd', action='store_true', help='Dump OSD memory')
    parser.add_argument('--upgrade', type=str, help='Upgrade baseband firmware')
    parser.add_argument('--download_firmware', type=str, help='Download firmware from baseband')
    parser.add_argument('--pulse_gpio', type=int, help='Pulse GPIO pin for <n> seconds')
    parser.add_argument('--read_meters', action='store_true', help='Show VU meter')
    parser.add_argument('--reboot', action='store_true', help='Reboot baseband')
    parser.add_argument('--load_preset', type=int, help='Load preset <n>')
    parser.add_argument('--store_preset', type=int, help='Store actual settings to preset <n>')
    parser.add_argument('--show_presets', action='store_true', help='Show all used presets')
    args = parser.parse_args()

    bb = Baseband()
    bb.connect_usb(serial=args.serial, description=args.description)

    if args.pulse_gpio:
        bb.pulse_gpio(args.pulse_gpio, 6)
        return 0  # If pulse gpio is requested, do not do anything else (the baseband will be rebooted)

    # Try to connect to the baseband
    bb.connect_baseband()

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
        print('\nPreset status (preset 0 stores the actual settings):')
        preset_flags = bb.load_preset_status()
        for i, flag in enumerate(preset_flags):
            print(f'Preset {i:2}: {bb.get_preset(i).name.decode() if flag else "Empty":14}', end='' if (i + 1) % 4 else '\n')

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
            serialized_settings = json.load(file)
        settings = bb.deserialize(serialized_settings, SETTINGS)
        bb.dump_settings(settings)
        bb.write_settings(settings)
        print(f'Settings read from {args.settings_from_file} and written to baseband')

    if args.dump_osd:
        bb.dump_osd_memory()

    if args.upgrade:
        with open(args.upgrade, 'rb') as file:
            firmware_data = file.read()
        bb.flash_firmware(firmware_data)

    if args.reboot:
        bb.reboot()

    if args.show_presets:
        preset_flags = bb.load_preset_status()
        for i, flag in enumerate(preset_flags):
            print(f'Preset {i}: {"Used" if flag else "Empty"}')
            if flag:
                bb.dump_settings(bb.get_preset(i))
                print()

    if args.load_preset:
        bb.load_preset(args.load_preset)
        print(f'Preset {args.load_preset} loaded')
        bb.dump_settings(bb.read_settings())

    if args.store_preset:
        settings = bb.read_settings()
        settings.name = f'Preset {args.store_preset}'.encode()
        bb.write_settings(settings)
        bb.store_preset(args.store_preset)
        bb.dump_settings(bb.read_settings())
        settings.name = f'Hallo'.encode()
        bb.write_settings(settings)
        print(f'Settings stored to preset {args.store_preset}')

if __name__ == '__main__':
    main()
"""
Baseband control class

(C) 2024 PE1OBW, PE1MUD
"""
import time
from ctypes import Array, Structure, sizeof
from typing import Any, Optional

from baseband.actuals import HW_INPUTS
from baseband.firmware_control import FirmwareControl
from baseband.info import INFO
from baseband.settings import AUDIO_INPUT, FM_BANDWIDTH, NICAM_BANDWIDTH, OSD_MODE, PREEMPHASIS, SETTINGS, VIDEO_IN, VIDEO_MODE

I2C_ACCESS_DISPLAY = bytearray([0x00, 0x00])  # R/W, maps to display memory, 40 columns x 16 rows = 640 bytes
I2C_ACCESS_FONT_MEMORY = bytearray([0x08, 0x00])  # R/W, maps to font memory, 128 characters, each 8x16 pixels = 2048 bytes
I2C_ACCESS_SETTINGS = bytearray([0x10, 0x00])  # R/W, maps to SETTINGS
I2C_ACCESS_READOUT = bytearray([0x20, 0x00])  # RO, maps to HW_INPUTS
I2C_ACCESS_COMMAND = bytearray([0x30, 0x00])  # R/W  maps to commands, read gives status (0=done), no auto address increment!
I2C_ACCESS_VIEW_SETTINGS = bytearray([0x40, 0x00])  # RO maps to SETTINGS preview (= the result from COMMAND_VIEW_PRESET)
I2C_ACCESS_READ_PRESET_STATUS = bytearray([0x50, 0x00])  # RO maps to PRESET_FLAGS, 32 bits (4 bytes), bit=1 indicates if a preset is used
I2C_ACCESS_INFO = bytearray([0x60, 0x00])  # RO	maps to INFO
I2C_ACCESS_FLASH = bytearray([0x70, 0x00])  # R/W maps to flash SPI interface, see description in file header

I2C_ACCESS_COMMAND_UPDATE_SETTINGS = bytearray([0x30, 0x00])  # <1> Update hardware registers (activate settings)
I2C_ACCESS_COMMAND_READ_PRESET = bytearray([0x30, 0x01])  # <preset nr> Read config from preset 1..31 and activate it
I2C_ACCESS_COMMAND_STORE_PRESET = bytearray([0x30, 0x02])  # <preset nr> Store current config in preset 1..31
I2C_ACCESS_COMMAND_ERASE_PRESET = bytearray([0x30, 0x03])  # <preset nr> Erase current config in preset 1..31
I2C_ACCESS_COMMAND_VIEW_PRESET = bytearray([0x30, 0x04])  # <preset nr> Read config from preset 1..31 and copy to 'preview' settings
I2C_ACCESS_COMMAND_REBOOT = bytearray([0x30, 0x05])  # <1> Reboot FPGA board after 500ms delay

# Helper to convert enums to strings and vice versa. The enum classes have the same name as fields in the SETTINGS struct.
SETTINGS_ENUMS = [VIDEO_MODE, VIDEO_IN, OSD_MODE, FM_BANDWIDTH, AUDIO_INPUT, PREEMPHASIS, NICAM_BANDWIDTH]


def enumstring_to_int(field_name: str, value: str) -> Any:
    """
    Convert a string to the correct enum type if applicable, else assume int.
    """
    for enum in SETTINGS_ENUMS:
        if field_name == enum.__name__.lower():
            try:
                return enum[value].value
            except KeyError:
                raise ValueError(f'Invalid value {value} for {field_name}, must be one of {", ".join([e.name for e in enum])}')
    return int(value)


class Baseband:
    """
    This class is responsible for providing methods to control the Baseband.
    """
    def __init__(self, usb_driver):
        self._slave = usb_driver

    def pulse_gpio(self, gpio_nr: int, seconds: int) -> None:
        print(f'Pulse GPIO pin {gpio_nr} for {seconds} seconds')
        self._slave.pulse_gpio(gpio_nr, seconds)

    def get_info(self) -> dict:
        """
        Get Baseband hw/sw version
        """
        result = self._slave.exchange(I2C_ACCESS_INFO, sizeof(INFO))
        info = INFO.from_buffer_copy(result)
        return {
            'hw_version': info.hw_version,
            'fpga_version': info.fpga_version,
            'sw_version': f'{info.sw_version_major}.{info.sw_version_minor}'
        }
    def read_settings(self) -> SETTINGS:
        """
        Get Baseband settings
        """
        raw_buffer = self._slave.exchange(I2C_ACCESS_SETTINGS, sizeof(SETTINGS))
        return SETTINGS.from_buffer_copy(raw_buffer)

    def write_settings(self, settings: SETTINGS) -> None:
        """
        Write Baseband settings
        """
        raw_buffer = bytearray(settings)
        self._slave.write(I2C_ACCESS_SETTINGS + raw_buffer)
        self._send_command(I2C_ACCESS_COMMAND_UPDATE_SETTINGS)

    def load_preset_status(self) -> list:
        """
        Get preset status
        """
        raw_buffer = self._slave.exchange(I2C_ACCESS_READ_PRESET_STATUS, 4)
        flags = int.from_bytes(raw_buffer, byteorder='little')
        return [flags & (1 << i) for i in range(32)]

    def get_preset(self, preset_nr: int) -> SETTINGS:
        """
        Read the contents of preset, without activating it
        """
        assert preset_nr > 0 and preset_nr < 32, f'Invalid preset number {preset_nr}'
        self._send_command(I2C_ACCESS_COMMAND_VIEW_PRESET, preset_nr)
        # Preset is now loaded in preview settings
        raw_buffer = self._slave.exchange(I2C_ACCESS_VIEW_SETTINGS, sizeof(SETTINGS))
        return SETTINGS.from_buffer_copy(raw_buffer)

    def load_preset(self, preset_nr: int) -> None:
        """
        Load a preset
        """
        assert preset_nr > 0 and preset_nr < 32, f'Invalid preset number {preset_nr}'
        self._send_command(I2C_ACCESS_COMMAND_READ_PRESET, preset_nr)

    def store_preset(self, preset_nr: int) -> None:
        """
        Store actual settings to a preset
        """
        assert preset_nr > 0 and preset_nr < 32, f'Invalid preset number {preset_nr}'
        self._send_command(I2C_ACCESS_COMMAND_STORE_PRESET, preset_nr)

    def erase_preset(self, preset_nr: int) -> None:
        """
        Erase a preset
        """
        assert preset_nr > 0 and preset_nr < 32, f'Invalid preset number {preset_nr}'
        self._send_command(I2C_ACCESS_COMMAND_ERASE_PRESET, preset_nr)

    def set_setting(self, setting_name: str, value: str) -> None:
        """
        Set a setting
        """
        # get current settings
        current = settings = self.read_settings()

        # convert dot-separated setting name to a path of field names
        # and try to find corresponding fields in the settings struct.
        setting_path = setting_name.split('.')
        while setting_path:
            path = setting_path.pop(0)
            found = False
            for field in current._fields_:
                field_name, field_type = field[0], field[1]
                if path == field_name:
                    found = True
                    if issubclass(field_type, Array) and issubclass(field_type._type_, Structure):
                        index = int(setting_path.pop(0))  # next element is the index
                        current = getattr(current, field_name)[index]
                    elif issubclass(field_type, Structure):
                        current = getattr(current, field_name)
                    else:
                        next_element = getattr(current, field_name)
                        if not isinstance(next_element, Structure):
                            if isinstance(next_element, int):
                                setattr(current, field_name, enumstring_to_int(field_name, value))
                            else:
                                setattr(current, field_name, value.encode('utf-8'))  # Convert to bytes
                            break
                        current = next_element
                    break
            if not found:
                raise ValueError(f'Invalid setting name {setting_name}, field {path} not found in {[field[0] for field in current._fields_]}')
        self.dump_settings(settings)
        self.write_settings(settings)

    def reboot(self) -> None:
        """
        Reboot the Baseband
        """
        self._send_command(I2C_ACCESS_COMMAND_REBOOT)

    def _send_command(self, command: int, param: int = 1) -> None:
        """
        Send a command to the baseband and wait until it's executed
        """
        POLL_TIMEOUT = 5
        POLL_REPEAT_INTERVAL = 0.01
        result = self._slave.exchange(command + bytearray([param]), 1)
        timeeout = POLL_TIMEOUT
        while not result[0] == 0x00 and timeeout > 0:
            result = self._slave.exchange(I2C_ACCESS_COMMAND_UPDATE_SETTINGS, 1)
            time.sleep(POLL_REPEAT_INTERVAL)
            timeeout -= POLL_REPEAT_INTERVAL

    @staticmethod
    def dump_settings(settings: SETTINGS) -> None:
        """
        Print the settings to the console
        """
        print(f'Setting name: {settings.name.decode()}')
        print(f'FM settings:')
        for i in range(0, 4):
            print(f'  {i+1}: rf_frequency_khz={settings.fm[i].rf_frequency_khz} kHz,'
                f' rf_level={settings.fm[i].rf_level},'
                f' input={AUDIO_INPUT(settings.fm[i].input).name},'
                f' preemphasis={PREEMPHASIS(settings.fm[i].preemphasis).name},'
                f' bw={FM_BANDWIDTH(settings.fm[i].bandwidth).name},', end='')
            print(f' am={settings.fm[i].am},' if i < 2 else '      ', end='')   # Only the first two can do AM
            print(f' enable={settings.fm[i].enable}')
        print(f'NICAM settings: {settings.nicam.rf_frequency_khz} kHz, level={settings.nicam.rf_level},'
            f' BW={NICAM_BANDWIDTH(settings.nicam.bandwidth).name}, input={settings.nicam.input}, ena={settings.nicam.enable}')
        print(f'VIDEO settings: video_level={settings.video.video_level}, video_mode={VIDEO_MODE(settings.video.video_mode).name}, '
              f'invert_video={settings.video.invert_video}, osd_mode={OSD_MODE(settings.video.osd_mode).name}, '
              f'input={VIDEO_IN(settings.video.video_in).name}, filter_bypass={settings.video.filter_bypass}, '
              f'ena={settings.video.enable}')
        print(f'GENERAL settings: audio1_extern_ena={settings.general.audio1_extern_ena}, audio2_extern_ena={settings.general.audio2_extern_ena}')

    def dump_osd_memory(self) -> None:
        """
        Read & print actual OSD contents
        """
        WIDTH = 40
        HEIGHT = 16
        result = self._slave.exchange(I2C_ACCESS_DISPLAY, WIDTH * HEIGHT)
        for y in range(0, HEIGHT):
            for x in range(0, WIDTH):
                print (f'{result[x + WIDTH * y]:02X}', end=' ')
            print('  [', end='')
            for x in range(0, WIDTH):
                i = x + WIDTH * y
                char = result[i] if result[i] >= 32 and result[i] < 127 else 32
                print (f'{chr(char)}', end='')
            print(']')


    def flash_firmware(self, firmware: bytes) -> None:
        """
        Upgrade Baseband firmware
        """
        firmware_control = FirmwareControl(self._slave)
        firmware_control.flash_firmware(firmware)

    def read_firmware(self) -> bytes:
        firmware_control = FirmwareControl(self._slave)
        return firmware_control.read_firmware()

    def read_actuals(self) -> HW_INPUTS:
        """
        Read actuals from the Baseband
        """
        raw_buffer = self._slave.exchange(I2C_ACCESS_READOUT, sizeof(HW_INPUTS))
        return HW_INPUTS.from_buffer_copy(raw_buffer)

    @staticmethod
    def serialize(structure_obj: Structure) -> dict:
        serialized_settings = {}
        for field in structure_obj._fields_:
            field_name = field[0]
            field_value = getattr(structure_obj, field_name)
            if isinstance(field_value, Structure):
                serialized_settings[field_name] = Baseband.serialize(field_value)
            elif hasattr(field_value, '_length_'):
                serialized_settings[field_name] = [Baseband.serialize(item) for item in field_value]
            else:
                if isinstance(field_value, bytes):
                    field_value = field_value.decode('utf-8')
                serialized_settings[field_name] = field_value
        return serialized_settings

    @staticmethod
    def deserialize(serialized_settings: str, structure: Structure, input: Optional[Structure] = None) -> Structure:
        """
        Create or update structure from json
        """
        obj = input or structure()
        for field in structure._fields_:
            field_name, field_type = field[0], field[1]
            if field_name in serialized_settings:
                field_value = serialized_settings[field_name]
                if issubclass(field_type, Structure):
                    setattr(obj, field_name, Baseband.deserialize(field_value, field_type))
                elif issubclass(field_type, Array) and issubclass(field_type._type_, Structure):
                    element_type = field_type._type_
                    for i, item in enumerate(field_value):
                        getattr(obj, field_name)[i] = Baseband.deserialize(item, element_type, getattr(obj, field_name)[i]) # if input else None)
                else:
                    # Basic type handling
                    if isinstance(field_value, str):
                        field_value = field_value.encode('utf-8')
                    setattr(obj, field_name, field_value)
        return obj

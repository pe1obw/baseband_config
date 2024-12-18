"""
Baseband control class

(C) 2024 PE1OBW, PE1MUD
"""
import time
from ctypes import Array, Structure, sizeof
from typing import Any, Optional, TypeVar

from baseband.actuals import HW_INPUTS
from baseband.firmware_control import FirmwareControl
from baseband.info import INFO
from baseband.settings import AUDIO_NCO_WAVEFORM, INPUT, AUDIO_NCO_MODE, FM_BANDWIDTH, INPUT_CH1, INPUT_CH2, NICAM_BANDWIDTH, OSD_MODE, PREEMPHASIS, SETTINGS, VIDEO_IN, VIDEO_MODE

I2C_ACCESS_DISPLAY = bytearray([0x00, 0x00])  # R/W, maps to display memory, 40 columns x 16 rows = 640 bytes
I2C_ACCESS_FONT_MEMORY = bytearray([0x08, 0x00])  # R/W, maps to font memory, 128 characters, each 8x16 pixels = 2048 bytes
I2C_ACCESS_SETTINGS = bytearray([0x10, 0x00])  # R/W, maps to SETTINGS
I2C_ACCESS_READOUT = bytearray([0x20, 0x00])  # RO, maps to HW_INPUTS
I2C_ACCESS_COMMAND = bytearray([0x30, 0x00])  # R/W  maps to commands, read gives status (0=done), no auto address increment!
I2C_ACCESS_VIEW_SETTINGS = bytearray([0x40, 0x00])  # RO maps to SETTINGS preview (= the result from COMMAND_VIEW_PRESET)
I2C_ACCESS_READ_PRESET_STATUS = bytearray([0x50, 0x00])  # RO maps to PRESET_FLAGS, 32 bits (4 bytes), bit=1 indicates if a preset is used
I2C_ACCESS_INFO = bytearray([0x60, 0x00])  # RO	maps to INFO
I2C_ACCESS_FLASH = bytearray([0x70, 0x00])  # R/W maps to flash SPI interface, see description in file header
I2C_ACCESS_PATTERN_MEMORY = bytearray([0x80, 0x00])  # R/W, maps to pattern memory (8192 bytes)
I2C_ACCESS_IO_REGISTERS = bytearray([0xA0, 0x00])  # R/W, maps to IO registers, see description in file header

I2C_ACCESS_COMMAND_UPDATE_SETTINGS = bytearray([0x30, 0x00])  # <1> Update hardware registers (activate settings)
I2C_ACCESS_COMMAND_READ_PRESET = bytearray([0x30, 0x01])  # <preset nr> Read config from preset 1..31 and activate it
I2C_ACCESS_COMMAND_STORE_PRESET = bytearray([0x30, 0x02])  # <preset nr> Store current config in preset 1..31
I2C_ACCESS_COMMAND_ERASE_PRESET = bytearray([0x30, 0x03])  # <preset nr> Erase current config in preset 1..31
I2C_ACCESS_COMMAND_VIEW_PRESET = bytearray([0x30, 0x04])  # <preset nr> Read config from preset 1..31 and copy to 'preview' settings
I2C_ACCESS_COMMAND_REBOOT = bytearray([0x30, 0x05])  # <1> Reboot FPGA board after 500ms delay
I2C_ACCESS_COMMAND_SET_DEFAULT = bytearray([0x30, 0x06])  # <1> Set actual settings to default

# Helper to convert enums to strings and vice versa. The enum classes have the same name as fields in the SETTINGS struct.
SETTINGS_ENUMS = [VIDEO_MODE, VIDEO_IN, OSD_MODE, FM_BANDWIDTH, INPUT, INPUT_CH1, INPUT_CH2, PREEMPHASIS, NICAM_BANDWIDTH, AUDIO_NCO_MODE, AUDIO_NCO_WAVEFORM]


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


T = TypeVar('T', bound=Structure)


class Baseband:
    """
    This class is responsible for providing methods to control the Baseband.
    """
    OSD_WIDTH = 40
    OSD_HEIGHT = 16

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

    def set_default(self) -> None:
        """
        Set actual settings to default
        """
        self._send_command(I2C_ACCESS_COMMAND_SET_DEFAULT)

    def set_using_name_value(self, settings: SETTINGS, setting_name: str, value: str) -> None:
        """
        Set a value by dot-separated setting name
        """
        current = settings

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
                    if issubclass(field_type, Array) and issubclass(field_type._type_, Structure):  # type: ignore
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

    def reboot(self) -> None:
        """
        Reboot the Baseband
        """
        self._send_command(I2C_ACCESS_COMMAND_REBOOT, nowait=True)

    def _send_command(self, command: bytearray, param: int = 1, nowait: bool = False) -> None:
        """
        Send a command to the baseband and wait until it's executed
        """
        POLL_TIMEOUT = 5
        POLL_REPEAT_INTERVAL = 0.01
        result = self._slave.exchange(command + bytearray([param]), 1)
        timeeout = POLL_TIMEOUT
        while (not nowait) and (not result[0] == 0x00) and timeeout > 0:
            result = self._slave.exchange(command, 1)
            time.sleep(POLL_REPEAT_INTERVAL)
            timeeout -= POLL_REPEAT_INTERVAL

    @staticmethod
    def dump_settings(settings: SETTINGS) -> None:
        """
        Print the settings to the console
        """
        print(f'Name: {settings.name.decode()}')
        print(f'VIDEO settings:\n'
              f'  video_level={settings.video.video_level}, video_mode={VIDEO_MODE(settings.video.video_mode).name},'
              f' invert_video={settings.video.invert_video}, osd_mode={OSD_MODE(settings.video.osd_mode).name}, show_menu={settings.video.show_menu},'
              f' video_in={VIDEO_IN(settings.video.video_in).name}, filter_bypass={settings.video.filter_bypass},'
              f' pattern_enable={settings.video.pattern_enable} enable={settings.video.enable}')
        print(f'NICAM settings:\n'
              f'  input_ch1={INPUT(settings.nicam.input_ch1).name}, input_ch2={INPUT(settings.nicam.input_ch2).name},'
              f' generator_level_ch1={settings.nicam.generator_level_ch1}, generator_level_ch2={settings.nicam.generator_level_ch2},'
              f' generator_ena_ch1={settings.nicam.generator_ena_ch1}, generator_ena_ch2={settings.nicam.generator_ena_ch2},\n'
              f'  rf_frequency_khz={settings.nicam.rf_frequency_khz} kHz, rf_level={settings.nicam.rf_level},'
              f' nicam_bandwidth={NICAM_BANDWIDTH(settings.nicam.nicam_bandwidth).name}, invert_spectrum={settings.nicam.invert_spectrum} enable={settings.nicam.enable}')
        print(f'FM settings:')
        for i in range(0, 4):
            print(f'  {i}: rf_frequency_khz={settings.fm[i].rf_frequency_khz} kHz,'
                f' rf_level={settings.fm[i].rf_level},'
                f' input={INPUT(settings.fm[i].input).name},'
                f' generator_ena={settings.fm[i].generator_ena},'
                f' generator_level={settings.fm[i].generator_level},'
                f' preemphasis={PREEMPHASIS(settings.fm[i].preemphasis).name},'
                f' fm_bandwidth={FM_BANDWIDTH(settings.fm[i].fm_bandwidth).name},', end='')
            print(f' am={settings.fm[i].am},' if i < 2 else '      ', end='')   # Only the first two can do AM
            print(f' enable={settings.fm[i].enable}')
        print(f'GENERAL settings:\n'
              f'  audio_nco_frequency={settings.general.audio_nco_frequency} Hz, audio_nco_mode={AUDIO_NCO_MODE(settings.general.audio_nco_mode).name},'
              f' audio_nco_waveform={AUDIO_NCO_WAVEFORM(settings.general.audio_nco_waveform).name},'
              f' morse_message "{settings.general.morse_message.decode()}", morse_speed={settings.general.morse_speed},'
              f' morse_message_repeat_time={settings.general.morse_message_repeat_time}\n'
              f'  last_recalled_presetnr={settings.general.last_recalled_presetnr}, user_setting1={settings.general.user_setting1}')

    def _handle_invert(self, str_in: str) -> str:
        """
        Handle invert command in OSD contents.
        Character values between \\i and \\u are inverted, i.e., 0x80 is added to the ASCII values.
        """
        start : int = 0
        out: str = str_in
        while True:
            start = str_in.find('\\i', start)
            if start == -1:
                break
            out = str_in[:start]
            start += 2  # Move to the character after the found substring
            end = str_in.find('\\u', start)
            if end == -1:
                end = len(str_in)
            # Invert the substring by adding 0x80 to the ASCII value of each character
            for c in str_in[start:end]:
                out += chr(ord(c) + 128)
            end += 2  # Move to the character after the found substring
            out += str_in[end:]
            start = end
        return out

    def write_osd(self, osd_contents: str) -> None:
        """
        Write to OSD.
        Replace substrings "\n" and "\0" with the actual line break and null character,
        truncate or pad with null characters to fit the 40x16 OSD memory.
        """
        osd_contents = osd_contents.replace('\\n', '\n').replace('\\0', '\0')
        for y, str in enumerate(osd_contents.split('\n')[:self.OSD_HEIGHT]):
            str = self._handle_invert(str)
            if len(str) > self.OSD_WIDTH:
                str = str[:self.OSD_WIDTH]
            else:
                str += '\0' * (self.OSD_WIDTH - len(str))
            osd_contents = osd_contents[:y * self.OSD_WIDTH] + str + osd_contents[(y + 1) * self.OSD_WIDTH:]
        self._slave.write(I2C_ACCESS_DISPLAY + bytes([ord(c) for c in osd_contents]))

    def clear_osd(self) -> None:
        """
        Clear OSD
        """
        contents = '\0' * self.OSD_WIDTH * self.OSD_HEIGHT
        self.write_osd(contents)

    def dump_osd_memory(self) -> None:
        """
        Read & print actual OSD contents
        """
        result = self._slave.exchange(I2C_ACCESS_DISPLAY, self.OSD_WIDTH * self.OSD_HEIGHT)
        for y in range(0, self.OSD_HEIGHT):
            for x in range(0, self.OSD_WIDTH):
                print (f'{result[x + self.OSD_WIDTH * y]:02X}', end=' ')
            print('  [', end='')
            for x in range(0, self.OSD_WIDTH):
                i = x + self.OSD_WIDTH * y
                char = result[i] if result[i] >= 32 and result[i] < 127 else 32
                print (f'{chr(char)}', end='')
            print(']')

    def read_pattern_memory(self) -> bytes:
        """
        Read pattern memory
        """
        return self._slave.exchange(I2C_ACCESS_PATTERN_MEMORY, 8192)

    def write_pattern_memory(self, pattern: bytes) -> None:
        """
        Write pattern memory
        """
        self._slave.write(I2C_ACCESS_PATTERN_MEMORY + pattern)

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
    def deserialize(serialized_settings: dict, structure: type[T], input: Optional[T] = None) -> T:
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
                elif issubclass(field_type, Array) and issubclass(field_type._type_, Structure):  # type: ignore
                    element_type = field_type._type_
                    for i, item in enumerate(field_value):
                        getattr(obj, field_name)[i] = Baseband.deserialize(item, element_type, getattr(obj, field_name)[i]) # if input else None)
                else:
                    # Basic type handling
                    if isinstance(field_value, str):
                        field_value = field_value.encode('utf-8')
                    setattr(obj, field_name, field_value)
        return obj

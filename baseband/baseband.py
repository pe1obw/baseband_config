"""
Baseband control class

(C) 2024 PE1OBW, PE1MUD
"""
import time
from ctypes import Array, Structure, sizeof

from baseband.actuals import HW_INPUTS
from baseband.firmware_control import FirmwareControl
from baseband.info import get_info
from baseband.osd import dump_osd_memory
from baseband.settings import AUDIO_INPUT, FM_BANDWIDTH, PREEMPHASIS, SETTINGS
from baseband.usb import get_device
from pyftdi.i2c import I2cController

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


class Baseband:
    """
    This class is responsible for providing methods to control the Baseband.
    """
    BB_SLAVE_ADDR = 0xB0//2
    I2C_FREQUENCY = 50000  # Increasing this results in read errors, due to a bug in the FT232H driver/HW. See <https://github.com/eblot/pyftdi/issues/373>

    def __init__(self):
        self._device = None
        self._i2c = None
        self._slave = None

    def connect_usb(self, serial=None, description=None):
        """
        Connect to the USB controller
        """
        self._device = get_device(serial, description)
        self._i2c = I2cController()
        self._i2c.configure(self._device, clockstretching=True, frequency=self.I2C_FREQUENCY)

    def connect_baseband(self):
        """
        Connect to the Baseband
        """
        self._slave = self._i2c.get_port(self.BB_SLAVE_ADDR)

    def pulse_gpio(self, gpio_nr: int, seconds: int) -> None:
        assert gpio_nr > 2 and gpio_nr < 7, f'Invalid GPIO number for FT232H {gpio_nr}'
        print(f'Pulse GPIO pin {gpio_nr} for {seconds} seconds')
        gpio = self._i2c.get_gpio()
        gpio.set_direction(pins=1 << gpio_nr, direction=1 << gpio_nr)  # GPIO 6 as output
        gpio.write(0)
        time.sleep(seconds)
        gpio.write(1 << gpio_nr)

    def get_info(self) -> dict:
        """
        Get Baseband hw/sw version
        """
        return get_info(self._slave)

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
        assert preset_nr >= 0 and preset_nr < 32, f'Invalid preset number {preset_nr}'
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
            print(f'  {i+1}: {settings.fm[i].rf_frequency_khz} kHz,'
                f' level={settings.fm[i].rf_level},'
                f' input={AUDIO_INPUT(settings.fm[i].input).name},'
                f' preemp={PREEMPHASIS(settings.fm[i].preemphasis).name},'
                f' bw={FM_BANDWIDTH(settings.fm[i].bandwidth).name},', end='')
            print(f' AM={settings.fm[i].am},' if i < 2 else '      ', end='')   # Only the first two can do AM
            print(f' Ena={settings.fm[i].enable}')
        print(f'NICAM settings: {settings.nicam.rf_frequency_khz} kHz, level={settings.nicam.rf_level},'
            f' BW={settings.nicam.bandwidth}, input={settings.nicam.input}, ena={settings.nicam.enable}')
        print(f'VIDEO settings: level={settings.video.video_level}, mode={settings.video.video_mode}, invert={settings.video.invert_video},'
            f' osd={settings.video.osd_mode}, input={settings.video.video_in}, ena={settings.video.enable}')

    def dump_osd_memory(self) -> None:
        """
        Read & print actual OSD contents
        """
        dump_osd_memory(self._slave)

    def flash_firmware(self, firmware: bytes) -> None:
        """
        Upgrade Baseband firmware
        """
        firmware_control = FirmwareControl(self._slave)
        firmware_control.flash_firmware(firmware)

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
    def deserialize(serialized_settings: str, structure: Structure) -> Structure:
        obj = structure()
        for field in structure._fields_:
            field_name, field_type = field[0], field[1]
            if field_name in serialized_settings:
                field_value = serialized_settings[field_name]
                if issubclass(field_type, Structure):
                    setattr(obj, field_name, Baseband.deserialize(field_value, field_type))
                elif issubclass(field_type, Array) and issubclass(field_type._type_, Structure):
                    # Check if it's an array of structures
                    element_type = field_type._type_
                    array_obj = field_type()
                    for i, item in enumerate(field_value):
                        array_obj[i] = Baseband.deserialize(item, element_type)
                    setattr(obj, field_name, array_obj)
                else:
                    # Basic type handling
                    if isinstance(field_value, str):
                        field_value = field_value.encode('utf-8')
                    setattr(obj, field_name, field_value)
        return obj

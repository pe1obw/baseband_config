"""
Read/write SDR settings.
Structs converted from .h file.

(C) 2024, 2026 PE1OBW, PE1MUD
"""
from ctypes import Structure, c_int16, c_uint16, c_uint32, c_char


I2C_ACCESS_SETTINGS = bytearray([0x10, 0x00])
I2C_ACCESS_COMMAND_UPDATE_SETTINGS = bytearray([0x30, 0x00])


class SDR_SETTINGS(Structure):
    _pack_ = 1
    _fields_ = [
        ("frequency_khz", c_uint32),
        ("gain_db", c_int16),
        ("bw_mhz", c_int16),
        ("bb_gain", c_int16),
        ("enable", c_uint16),
        ("fir_filter_mhz", c_uint16),
    ]

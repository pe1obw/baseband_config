"""
Read/write SDR settings.
Structs converted from .h file.

(C) 2024, 2026 PE1OBW, PE1MUD
"""
from ctypes import Structure, c_int16, c_int8, c_uint32, c_uint8


I2C_ACCESS_SETTINGS = bytearray([0x10, 0x00])
I2C_ACCESS_COMMAND_UPDATE_SETTINGS = bytearray([0x30, 0x00])


class SDR_SETTINGS(Structure):
    _pack_ = 1
    _fields_ = [
        ("frequency_khz", c_uint32),
        ("gain_db", c_int8),
        ("bw_mhz", c_uint8),
        ("bb_gain", c_int16),
        ("enable", c_uint8),
        ("fir_filter_mhz", c_uint8),
        ("spectrum_invert", c_uint8),
        ("output_channel", c_uint8),
        ("tx_mode", c_uint8),
        ("power_on_mode", c_uint8),
        ("enable_hpf", c_uint8),
    ]

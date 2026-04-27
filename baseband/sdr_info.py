"""
Read SDR info from the device

(C) 2024, 2026 PE1OBW, PE1MUD
"""
from ctypes import Structure, c_uint8

I2C_ACCESS_INFO = bytearray([0x60, 0x00])


class SDR_INFO(Structure):
    _pack_ = 1
    _fields_ = [
        ("sw_version_major", c_uint8),
        ("sw_version_minor", c_uint8),
        ("sw_version_patch", c_uint8),
        ("sw_version_dirty", c_uint8),
        ("ad9361_temperature", c_uint8),
        ("zynq_temperature", c_uint8)
    ]

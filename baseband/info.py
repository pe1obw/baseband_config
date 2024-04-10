"""
Read Baseband info from the device

(C) 2024 PE1OBW, PE1MUD
"""
from ctypes import Structure, c_uint8
from pyftdi.i2c import I2cPort

I2C_ACCESS_INFO = bytearray([0x60, 0x00])


class INFO(Structure):
    _pack_ = 1
    _fields_ = [
        ("hw_version", c_uint8),
        ("fpga_version", c_uint8),
        ("sw_version_minor", c_uint8),
        ("sw_version_major", c_uint8)
    ]


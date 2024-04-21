"""
Read/write baseband settings.
Structs converted from .h file.

(C) 2024 PE1OBW, PE1MUD
"""
from ctypes import Structure, c_uint16, c_uint8, c_char
from enum import Enum


I2C_ACCESS_SETTINGS = bytearray([0x10, 0x00])
I2C_ACCESS_COMMAND_UPDATE_SETTINGS = bytearray([0x30, 0x00])


class VIDEO_MODE(Enum):
    FLAT, PAL, NTSC, SECAM = range(4)


class VIDEO_IN(Enum):
    VIDEO_IN, VIDEO_GENERATOR, VIDEO_IN_AUTO = range(3)


class OSD_MODE(Enum):
    OSD_OFF, OSD_ON, OSD_AUTO = range(3)


class FM_BANDWIDTH(Enum):
    BW_130, BW_180, BW_230, BW_280 = range(4)


class AUDIO_INPUT(Enum):
    IN1L, IN1R, IN2L, IN2R, IN1LR, IN2LR = range(6)


class PREEMPHASIS(Enum):
    AUDIO_50US, AUDIO_75US, AUDIO_J17, AUDIO_FLAT = range(4)


class NICAM_BANDWIDTH(Enum):
    BW_700, BW_500 = range(2)


class FM_SETTINGS(Structure):
    _pack_ = 1
    _fields_ = [
        ("rf_frequency_khz", c_uint16),
        ("rf_level", c_uint16),
        ("input", c_uint16, 3),
        ("preemphasis", c_uint16, 2),
        ("bandwidth", c_uint16, 3),
        ("am", c_uint16, 1),
        ("enable", c_uint16, 1)
    ]


class NICAM_SETTINGS(Structure):
    _pack_ = 1
    _fields_ = [
        ("rf_frequency_khz", c_uint16),
        ("rf_level", c_uint16),
        ("bandwidth", c_uint8, 1),
        ("input", c_uint8, 3),
        ("enable", c_uint8, 1)
    ]


class VIDEO_SETTINGS(Structure):
    _pack_ = 1
    _fields_ = [
        ("video_level", c_uint16, 8),
        ("video_mode", c_uint16, 2),
        ("invert_video", c_uint16, 1),
        ("osd_mode", c_uint16, 2),
        ("video_in", c_uint16, 2),
        ("filter_bypass", c_uint16, 1),
        ("show_menu", c_uint8, 1),
        ("enable", c_uint8, 1)
    ]

class GENERAL_SETTINGS(Structure):
    _pack_ = 1
    _fields_ = [
        ("audio1_extern_ena", c_uint8, 1),
        ("audio2_extern_ena", c_uint8, 1)
    ]

class SETTINGS(Structure):
    _pack_ = 1
    _fields_ = [
        ("name", c_char*12),
        ("fm", FM_SETTINGS*4),
        ("nicam", NICAM_SETTINGS),
        ("video", VIDEO_SETTINGS),
        ("general", GENERAL_SETTINGS)
    ]

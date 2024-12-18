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


class INPUT(Enum):
    ADC1L, ADC1R, ADC2L, ADC2R, I2S1L, I2S1R, I2S2L, I2S2R, ADC1LR, ADC2LR, I2S1LR, I2S2LR, MUTE = range(13)


class INPUT_CH1(Enum):
    ADC1L, ADC1R, ADC2L, ADC2R, I2S1L, I2S1R, I2S2L, I2S2R, ADC1LR, ADC2LR, I2S1LR, I2S2LR, MUTE = range(13)


class INPUT_CH2(Enum):
    ADC1L, ADC1R, ADC2L, ADC2R, I2S1L, I2S1R, I2S2L, I2S2R, ADC1LR, ADC2LR, I2S1LR, I2S2LR, MUTE = range(13)


class PREEMPHASIS(Enum):
    AUDIO_50US, AUDIO_75US, AUDIO_J17, AUDIO_FLAT = range(4)


class NICAM_BANDWIDTH(Enum):
    BW_700, BW_500 = range(2)


class AUDIO_NCO_MODE(Enum):
    NCO_CW, NCO_MORSE = range(2)


class AUDIO_NCO_WAVEFORM(Enum):
    NCO_SINE, NCO_SQUARE, NCO_NOISE = range(3)


class FM_SETTINGS(Structure):
    _pack_ = 1
    _fields_ = [
        ("rf_frequency_khz", c_uint16),
        ("rf_level", c_uint16),
        ("input", c_uint16, 4),
        ("preemphasis", c_uint16, 2),
        ("fm_bandwidth", c_uint16, 3),
        ("generator_ena", c_uint16, 1),
        ("generator_level", c_uint16, 4),
        ("am", c_uint16, 1),
        ("enable", c_uint16, 1)
    ]

class NICAM_SETTINGS(Structure):
    _pack_ = 1
    _fields_ = [
        ("rf_frequency_khz", c_uint16),
        ("rf_level", c_uint16),
        ("input_ch1", c_uint8, 4),
        ("input_ch2", c_uint8, 4),
        ("generator_level_ch1", c_uint8, 4),
        ("generator_level_ch2", c_uint8, 4),
        ("generator_ena_ch1", c_uint8, 1),
        ("generator_ena_ch2", c_uint8, 1),
        ("nicam_bandwidth", c_uint8, 1),
        ("enable", c_uint8, 1),
        ("invert_spectrum", c_uint8, 1)
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
        ("pattern_enable", c_uint8, 1),
        ("enable", c_uint8, 1)
    ]


class GENERAL_SETTINGS(Structure):
    _pack_ = 1
    _fields_ = [
        ("morse_message", c_char*16),
        ("audio_nco_frequency", c_uint16, 14),
        ("audio_nco_waveform", c_uint16, 2),
        ("audio_nco_mode", c_uint16, 2),
        ("morse_speed", c_uint16, 2),
        ("morse_message_repeat_time", c_uint16, 10),
        ("spare", c_uint16, 2),
        ("last_recalled_presetnr", c_uint16, 8),
        ("user_setting1", c_uint16, 8)
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

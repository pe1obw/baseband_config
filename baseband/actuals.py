"""
Structures with actual hardware values, converted to Python ctypes

(C) 2024 PE1OBW, PE1MUD
"""
from ctypes import Structure, c_uint16, c_uint32

class HW_INPUTS(Structure):
    _pack_ = 1
    _fields_ = [
        ("adc1_left_audio_peak", c_uint16),
        ("adc1_right_audio_peak", c_uint16),
        ("adc2_left_audio_peak", c_uint16),
        ("adc2_right_audio_peak", c_uint16),
        ("fm1_audio_peak", c_uint16),
        ("fm2_audio_peak", c_uint16),
        ("fm3_audio_peak", c_uint16),
        ("fm4_audio_peak", c_uint16),
        ("vid_adc_clip", c_uint32, 1),
        ("vid_low_pass_clip", c_uint32, 1),
        ("vid_preemp_clip", c_uint32, 1),
        ("nicam_upsampling_clip", c_uint32, 1),
        ("baseband_clip", c_uint32, 1),
        ("spare1", c_uint32, 27),
        ("adc_in_min", c_uint16),
        ("adc_in_max", c_uint16),
        ("dac_out_min", c_uint16),
        ("dac_out_max", c_uint16),
        ("nicam_reset", c_uint32, 1),
        ("baseband_pll_locked", c_uint32, 1),
        ("spare2", c_uint32, 30),
        ("nicam_left_peak", c_uint16),
        ("nicam_right_peak", c_uint16)
    ]

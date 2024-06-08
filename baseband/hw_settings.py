'''
HW_SETTINGS is a structure that directly maps to the hardware registers in the FPGA.
'''
from ctypes import Structure, c_uint16, c_uint32


class HW_SETTINGS(Structure):
    _pack_ = 1
    _fields_ = [
        ("video_preemp_a1", c_uint16),
        ("video_preemp_a2", c_uint16),

        ("video_preemp_b0", c_uint16),
        ("video_preemp_b1", c_uint16),

        ("video_preemp_b2", c_uint16),
        ("spare", c_uint16),

        ("fm1_carrier_frequency", c_uint32),
        ("fm2_carrier_frequency", c_uint32),
        ("fm3_carrier_frequency", c_uint32),
        ("fm4_carrier_frequency", c_uint32),

        ("fm1_level", c_uint16, 10),
        ("fm1_spare", c_uint16, 4),
        ("fm1_fm_ena", c_uint16, 1),
        ("fm1_am_ena", c_uint16, 1),
        ("fm2_level", c_uint16, 10),
        ("fm2_spare", c_uint16, 4),
        ("fm2_fm_ena", c_uint16, 1),
        ("fm2_am_ena", c_uint16, 1),

        ("fm3_level", c_uint16, 10),
        ("fm3_spare", c_uint16, 4),
        ("fm3_fm_ena", c_uint16, 1),
        ("fm3_am_ena", c_uint16, 1),
        ("fm4_level", c_uint16, 10),
        ("fm4_spare", c_uint16, 4),
        ("fm4_fm_ena", c_uint16, 1),
        ("fm4_am_ena", c_uint16, 1),

        ("fm_spare", c_uint32, 16),
        ("fm1_preemp", c_uint32, 2),
        ("fm1_bandwidth", c_uint32, 2),
        ("fm2_preemp", c_uint32, 2),
        ("fm2_bandwidth", c_uint32, 2),
        ("fm3_preemp", c_uint32, 2),
        ("fm3_bandwidth", c_uint32, 2),
        ("fm4_preemp", c_uint32, 2),
        ("fm4_bandwidth", c_uint32, 2),

        ("nicam_frequency", c_uint32, 11),
        ("nicam_control", c_uint32, 4),
        ("nicam_mode", c_uint32, 2),
        ("nicam_scramble_init", c_uint32, 9),
        ("spare2", c_uint32, 6),

        ("nicam_level", c_uint16),
        ("reg11b", c_uint16),

        ("audio_nco_frequency", c_uint32, 14),
        ("audio_nco_waveform", c_uint32, 2),
        ("reg12_spare", c_uint16),

        ("reg13", c_uint32),

        ("reg14", c_uint32),

        ("video_overlay_enable", c_uint32, 1),
        ("reset_peaks", c_uint32, 1),
        ("generator_enable", c_uint32, 1),
        ("video_filter_bypass", c_uint32, 1),
        ("spare3", c_uint32, 28)
    ]
"""
Test all settings using the CLI
"""

import os
import unittest


class TestCliSettings(unittest.TestCase):
    """
    Test changing settings using the --set command
    """
    def _system(self, cmd: str) -> int:
        """
        Run a system command, return the exit code
        """
        if os.name == 'nt':
            return os.system(f"{cmd} > nul 2>&1")
        else:
            return os.system(f"{cmd} > /dev/null 2>&1")

    def test_fm(self):
        """
        Test FM settings
        """
        # Go over FM channel 0..3, set all to default
        settings: list[dict] = [
        {
            "rf_frequency_khz": 7020,
            "rf_level": 100,
            "input": "ADC1L",
            "generator_ena": 0,
            "generator_level": 2,
            "preemphasis": "AUDIO_50US",
            "fm_bandwidth": "BW_130",
            "am": 0,
            "enable": 1
        },
        {
            "rf_frequency_khz": 7200,
            "rf_level": 100,
            "input": "ADC1R",
            "generator_ena": 0,
            "generator_level": 2,
            "preemphasis": "AUDIO_50US",
            "fm_bandwidth": "BW_130",
            "am": 0,
            "enable": 1
        },
        {
            "rf_frequency_khz": 7380,
            "rf_level": 100,
            "input": "ADC2L",
            "generator_ena": 0,
            "generator_level": 2,
            "preemphasis": "AUDIO_50US",
            "fm_bandwidth": "BW_130",
            "am": 0,
            "enable": 1
        },
        {
            "rf_frequency_khz": 7560,
            "rf_level": 100,
            "input": "ADC2R",
            "generator_ena": 0,
            "generator_level": 2,
            "preemphasis": "AUDIO_50US",
            "fm_bandwidth": "BW_130",
            "am": 0,
            "enable": 1
        }
        ]

        for fm_ch in range(0, 4):
            for key, value in settings[fm_ch].items():
                self.assertEqual(self._system(f"baseband_config --usb_easymcp --set fm.{fm_ch}.{key}={value}"), 0,
                                 f"Failed to set {key}={value} on FM channel {fm_ch}")

    def test_nicam(self):
        """
        Test all NICAM settings
        NICAM settings:
            input_ch1=ADC1L, input_ch2=ADC1R, generator_level_ch1=2, generator_level_ch2=2, generator_ena_ch1=0, generator_ena_ch2=0,
            rf_frequency_khz=6552, rf_level=200, nicam_bandwidth=BW_700, enable=1
        """
        settings: dict = {
            "input_ch1": "ADC1L",
            "input_ch2": "ADC1R",
            "generator_level_ch1": 2,
            "generator_level_ch2": 2,
            "generator_ena_ch1": 0,
            "generator_ena_ch2": 0,
            "rf_frequency_khz": 6552,
            "rf_level": 200,
            "nicam_bandwidth": "BW_700",
            "enable": 1
        }
        for key, value in settings.items():
            self.assertEqual(self._system(f"baseband_config --usb_easymcp --set nicam.{key}={value}"), 0,
                             f"Failed to set {key}={value} on NICAM settings")

    def test_video(self):
        """
        Test all video settings
        VIDEO settings: video_level=110, video_mode=FLAT, invert_video=0, osd_mode=OSD_AUTO, show_menu=1, video_in=VIDEO_IN_AUTO, filter_bypass=0, ena=1
        """
        settings: dict = {
            "video_level": 92,
            "video_mode": "PAL",
            "invert_video": 0,
            "osd_mode": "OSD_AUTO",
            "show_menu": 1,
            "video_in": "VIDEO_IN_AUTO",
            "filter_bypass": 0,
            "enable": 1
        }
        for key, value in settings.items():
            self.assertEqual(self._system(f"baseband_config --usb_easymcp --set video.{key}={value}"), 0,
                             f"Failed to set {key}={value} on VIDEO settings")

    def test_general(self):
        """
        Test general settings
        GENERAL settings:
            audio_nco_frequency=500, audio_nco_mode=NCO_MORSE,
            morse_message "Baseband", morse_speed=1, morse_message_repeat_time=10
        """
        settings: dict = {
            "audio_nco_frequency": 500,
            "audio_nco_mode": "NCO_MORSE",
            "morse_message": "Baseband",
            "morse_speed": 1,
            "morse_message_repeat_time": 10
        }
        for key, value in settings.items():
            self.assertEqual(self._system(f"baseband_config --usb_easymcp --set general.{key}={value}"), 0,
                             f"Failed to set {key}={value} on GENERAL settings")


if __name__ == '__main__':
    unittest.main()
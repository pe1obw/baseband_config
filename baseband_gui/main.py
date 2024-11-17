"""
Simple GUI for configuring the baseband board

(C) 2024 PE1OBW, PE1MUD
"""
import logging
import math
import tkinter as tk

import customtkinter
from nicam_dialog import NicamDialog

from baseband.baseband import Baseband
from baseband.usb_easymcp import UsbEasyMcp
from baseband.usb_ftdi import UsbFtdi
from baseband.usb_mcp2221 import UsbMcp2221

logger = logging.getLogger(__name__)

NR_FM_CARRIERS = 4
PEAK_FS = 32768
FM_PEAK_FS = 1024


def to_log(value: float) -> float:
    """
    for inputs between 0 and 1, convert to dB and scale to 0 (-80dBFS) to 1 (0dBFS)
    """
    if value == 0.0:
        return 0
    vu = max(0, (20 * math.log10(value) / 80) + 1)
    return vu


def read_pattern_file(filename):
    '''
    Read pattern memory from file
    format is <addr>: <data> ... <data> (20 bytes)
    0000: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
    '''
    buffer = [0] * 8192
    with open(filename, 'rt') as file:
        for line in file.readlines():
            line = line.rstrip('\n').rstrip('\r')
            # Check format
            if len(line) < 6 or line[4] != ':':
                continue
            # Parse address
            address = int(line[:4], 16)
            # Parse data
            data = line[6:].split()
            for byte in data:
                buffer[address] = int(byte, 16)
                address += 1
    return buffer


class Gui(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self._baseband = None
        self._settings = None
        self._nicam_dialog = None
        self._usb_type = 'EasyMCP2221'
        self._construct_main_dialog()

    def _construct_main_dialog(self):
        VU_COLOR = 'green'
        VU_WIDTH = 200
        YPAD = 2
        SETTING_WIDTH = 15
        SETTING_TEXT = 'Setup'

        self.title('Baseband settings')
        self.geometry('600x500')
        # self.resizable(False, False)
        self.grid_columnconfigure(0, weight=1)

        # Connections
        self._frame = customtkinter.CTkFrame(self)
        self._frame.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="nsw")

        self._settings_button = customtkinter.CTkButton(self._frame, text='Interface', command=self._settings_dialog)
        self._settings_button.grid(row=0, column=0, padx=20, pady=10)

        self._connect_button = customtkinter.CTkButton(self._frame, text='Connect', command=self._connect)
        self._connect_button.grid(row=0, column=1, padx=20, pady=10)

        self._info_label = customtkinter.CTkLabel(self._frame, text='Not connected')
        self._info_label.grid(row=0, column=2, padx=20, pady=10)

        self._frame = customtkinter.CTkFrame(self)
        self._frame.grid(row=1, column=0, padx=10, pady=(10, 0), sticky="nsw")
        self._frame_label = customtkinter.CTkLabel(self._frame, text='Inputs')
        self._frame_label.grid(row=0, column=0, padx=20, pady=YPAD, columnspan=3)

        self._video_label = customtkinter.CTkLabel(self._frame, text='Video')
        self._video_label.grid(row=1, column=0, padx=20, pady=YPAD)
        self._video_meter = customtkinter.CTkProgressBar(self._frame, width=VU_WIDTH, progress_color=VU_COLOR)
        self._video_meter.grid(row=1, column=1, padx=20, pady=YPAD)
        self._video_meter.set(0.1)
        self._video_settings = customtkinter.CTkButton(self._frame, text=SETTING_TEXT, command=self._settings_dialog, width=SETTING_WIDTH)
        self._video_settings.grid(row=1, column=2, padx=20, pady=YPAD)

        self._nicam_label = customtkinter.CTkLabel(self._frame, text='NICAM')
        self._nicam_label.grid(row=2, column=0, padx=20, pady=0)
        self._nicam_meter_l = customtkinter.CTkProgressBar(self._frame, width=VU_WIDTH, progress_color=VU_COLOR)
        self._nicam_meter_l.grid(row=2, column=1, padx=20, pady=0)
        self._nicam_meter_l.set(0.5)
        self._nicam_label2 = customtkinter.CTkLabel(self._frame, text='')
        self._nicam_label2.grid(row=3, column=0, padx=20, pady=0)
        self._nicam_meter_r = customtkinter.CTkProgressBar(self._frame, width=VU_WIDTH, progress_color=VU_COLOR)
        self._nicam_meter_r.grid(row=3, column=1, padx=20, pady=0)
        self._nicam_meter_r.set(0.2)
        self._nicam_settings = customtkinter.CTkButton(self._frame, text=SETTING_TEXT, command=self._nicam_settings_dialog, width=SETTING_WIDTH)
        self._nicam_settings.grid(row=2, column=2, padx=20, pady=0)

        self._fm_label = []
        self._fm_meter = []
        self._fm_settings = []
        for i in range(NR_FM_CARRIERS):
            self._fm_label.append(customtkinter.CTkLabel(self._frame, text=f'FM {i+1}'))
            self._fm_label[i].grid(row=4+i, column=0, padx=20, pady=YPAD)
            self._fm_meter.append(customtkinter.CTkProgressBar(self._frame, width=VU_WIDTH, progress_color=VU_COLOR))
            self._fm_meter[i].grid(row=4+i, column=1, padx=20, pady=YPAD)
            self._fm_meter[i].set(0.1 * i)
            self._fm_settings.append(customtkinter.CTkButton(self._frame, text=SETTING_TEXT, command=self._settings_dialog, width=SETTING_WIDTH))
            self._fm_settings[i].grid(row=4+i, column=2, padx=20, pady=YPAD)

    def _nicam_settings_dialog(self):
        if self._nicam_dialog is None or not self._nicam_dialog.winfo_exists():
            self._nicam_dialog = NicamDialog(self)
        self._nicam_dialog.update_settings(self._settings)
        self._nicam_dialog.focus()
        self._nicam_dialog.after(0, self._nicam_dialog.lift)  # hack!

    def _connect(self):
        if self._baseband is None:
            if self._usb_type == 'FTDI':
                usb_driver = UsbMcp2221()
            elif self._usb_type == 'EasyMCP2221':
                usb_driver = UsbEasyMcp()
            else:
                usb_driver = UsbFtdi()
            logger.info(f'Connecting to baseband board using {usb_driver.__class__.__name__}')
            self._baseband = Baseband(usb_driver)
            info = self._baseband.get_info()

            info = (f'Hardware version: {info["hw_version"]}\n'
                    f'FPGA version: {info["fpga_version"]}\n'
                    f'Software version: {info["sw_version"]}{" (bootloader, no image!)" if info["sw_version"] == "0.0" else ""}')
            self._info_label.configure(text=info)

            self._settings = self._baseband.read_settings()
            self._update_settings()

            self._timer = self.after(1000, self._update_vu_meters)

    def _update_settings(self):
        if self._nicam_dialog is not None and self._nicam_dialog.winfo_exists():
            self._nicam_dialog.update_settings(self._settings)

    def _update_vu_meters(self):
        if self._baseband is not None:
            actuals = self._baseband.read_actuals()
            self._video_meter.set((actuals.adc_in_max - actuals.adc_in_min) / 1024)
            self._nicam_meter_l.set(to_log(actuals.adc1_left_audio_peak / PEAK_FS))
            self._nicam_meter_r.set(to_log(actuals.adc1_right_audio_peak / PEAK_FS))
            for i in range(NR_FM_CARRIERS):
                fm_level = getattr(actuals, f'fm{i+1}_audio_peak') / FM_PEAK_FS
                self._fm_meter[i].set(to_log(fm_level))
            self._timer = self.after(1000, self._update_vu_meters)

    def _new_usb_type(self, event):
        self._usb_type = self._usb_combobox.get()

    def _settings_dialog(self):
        dialog = tk.Toplevel(self)

        # Create 'USB interface' label
        usb_label = tk.Label(dialog, text='USB interface:')
        usb_label.grid(row=0, column=0, padx=20, pady=10)

        # Create combobox
        self._usb_combobox = customtkinter.CTkComboBox(dialog, values=['FTDI', 'EasyMCP2221'], state='readonly')
        self._usb_combobox.grid(row=0, column=1, padx=20, pady=10)
        self._usb_combobox.set('FTDI')
        self._usb_combobox.configure(command=self._new_usb_type)

        # Create 'Close' button. On click, close dialog
        close_button = customtkinter.CTkButton(dialog, text='Close', command=dialog.destroy)
        close_button.grid(row=1, column=1, padx=20, pady=10)


if __name__ == '__main__':
    gui = Gui()
    gui.mainloop()
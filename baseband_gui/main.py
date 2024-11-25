"""
Simple GUI for configuring the baseband board

(C) 2024 PE1OBW, PE1MUD
"""
import logging
import math
import tkinter as tk
from typing import Optional

import customtkinter
from CTkMessagebox import CTkMessagebox

from baseband.baseband import Baseband
from baseband.settings import NR_FM_CARRIERS
from baseband.usb_easymcp import UsbEasyMcp
from baseband.usb_ftdi import UsbFtdi
from baseband.usb_mcp2221 import UsbMcp2221
from baseband_gui.fm_dialog import FmDialog
from baseband_gui.generator_dialog import GeneratorDialog
from baseband_gui.nicam_dialog import NicamDialog
from baseband_gui.video_dialog import VideoDialog

logger = logging.getLogger(__name__)

PEAK_FS = 32768
FM_PEAK_FS = 1024
BASEBAND_UPDATE_RATE = 100  # in ms

SET_DEFAULTS = 'Set defaults'
FLAT_WITH_OSD = 'Flat with OSD'


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
        self._timer = None
        self._video_dialog: Optional[VideoDialog] = None
        self._nicam_dialog: Optional[NicamDialog] = None
        self._fm_dialog: list[Optional[FmDialog]] = [None] * NR_FM_CARRIERS
        self._generator_dialog: Optional[GeneratorDialog] = None
        self._usb_type = 'EasyMCP2221'
        self._construct_main_dialog()

    @property
    def _all_dialogs(self):
        return [self._video_dialog, self._nicam_dialog, self._generator_dialog] + self._fm_dialog

    def _construct_main_dialog(self):
        VU_COLOR = 'green'
        VU_WIDTH = 200
        YPAD = 2
        BUTTON_WIDTH = 15
        SETTING_TEXT = 'Setup'

        self.title('Baseband settings')
        self.geometry('750x500')
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

        # Inputs
        self._frame = customtkinter.CTkFrame(self)
        self._frame.grid(row=1, column=0, padx=10, pady=(10, 0), sticky="nsw")
        self._frame_label = customtkinter.CTkLabel(self._frame, text='Inputs')
        self._frame_label.grid(row=0, column=0, padx=20, pady=YPAD, columnspan=3)

        self._video_label = customtkinter.CTkLabel(self._frame, text='Video')
        self._video_label.grid(row=1, column=0, padx=20, pady=YPAD)
        self._video_meter = customtkinter.CTkProgressBar(self._frame, width=VU_WIDTH, progress_color=VU_COLOR)
        self._video_meter.grid(row=1, column=1, padx=20, pady=YPAD)
        self._video_meter.set(0.1)
        self._video_settings = customtkinter.CTkButton(self._frame, text=SETTING_TEXT, command=self._video_settings_dialog, width=BUTTON_WIDTH)
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
        self._nicam_settings = customtkinter.CTkButton(self._frame, text=SETTING_TEXT, command=self._nicam_settings_dialog, width=BUTTON_WIDTH)
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
            self._fm_settings.append(customtkinter.CTkButton(self._frame, text=SETTING_TEXT, command=lambda i=i: self._fm_settings_dialog(i),
                                                             width=BUTTON_WIDTH))
            self._fm_settings[i].grid(row=4+i, column=2, padx=20, pady=YPAD)

        self._audio_generator_label = customtkinter.CTkLabel(self._frame, text='Audio generator')
        self._audio_generator_label.grid(row=8, column=0, padx=20, pady=YPAD)
        self._audio_generator_settings = customtkinter.CTkButton(self._frame, text=SETTING_TEXT, command=self._generator_settings_dialog, width=BUTTON_WIDTH)
        self._audio_generator_settings.grid(row=8, column=1, padx=20, pady=YPAD, sticky='w')

        # Presets
        self._frame = customtkinter.CTkFrame(self)
        self._frame.grid(row=2, column=0, padx=10, pady=(10, 0), sticky="nsw")
        self._frame_label = customtkinter.CTkLabel(self._frame, text='Presets')
        self._frame_label.grid(row=0, column=0, padx=20, pady=YPAD, columnspan=3)

        presets = [SET_DEFAULTS, FLAT_WITH_OSD]
        self._load_preset_label = customtkinter.CTkLabel(self._frame, text='Preset')
        self._load_preset_label.grid(row=1, column=0, padx=20, pady=YPAD)
        self._selected_preset = customtkinter.CTkComboBox(self._frame, width=VU_WIDTH, values=presets, state='readonly')
        self._selected_preset.grid(row=1, column=1, padx=20, pady=YPAD)
        self._selected_preset.set(presets[0])
        self._load_preset_button = customtkinter.CTkButton(self._frame, text='Load', width=BUTTON_WIDTH, command=self._load_preset)
        self._load_preset_button.grid(row=1, column=2, padx=20, pady=YPAD)

    def _video_settings_dialog(self):
        if self._video_dialog is None or not self._video_dialog.winfo_exists():
            self._video_dialog = VideoDialog(self)
        self._video_dialog.update_controls(self._settings)
        self._video_dialog.focus()
        self._video_dialog.after(0, self._video_dialog.lift)  # hack!

    def _nicam_settings_dialog(self):
        if self._nicam_dialog is None or not self._nicam_dialog.winfo_exists():
            self._nicam_dialog = NicamDialog(self)
        self._nicam_dialog.update_controls(self._settings)
        self._nicam_dialog.focus()
        self._nicam_dialog.after(0, self._nicam_dialog.lift)  # hack!

    def _fm_settings_dialog(self, index: int):
        dialog = self._fm_dialog[index]
        if dialog is None or not dialog.winfo_exists():
            dialog = FmDialog(self, carrier_index=index)
        dialog.update_controls(self._settings)
        dialog.focus()
        dialog.after(0, dialog.lift)
        self._fm_dialog[index] = dialog

    def _generator_settings_dialog(self):
        if self._generator_dialog is None or not self._generator_dialog.winfo_exists():
            self._generator_dialog = GeneratorDialog(self)
        self._generator_dialog.update_controls(self._settings)
        self._generator_dialog.focus()
        self._generator_dialog.after(0, self._generator_dialog.lift)  # hack!

    def _connect(self):
        if self._baseband is None:
            try:
                if self._usb_type == 'FTDI':
                    usb_driver = UsbMcp2221()
                elif self._usb_type == 'EasyMCP2221':
                    usb_driver = UsbEasyMcp()
                else:
                    usb_driver = UsbFtdi()
                assert usb_driver is not None
                logger.info(f'Connecting to baseband board using {usb_driver.__class__.__name__}')
                baseband = Baseband(usb_driver)
                info = baseband.get_info()
            except Exception as e:
                logger.error(f'Error connecting to baseband board: {e}')
                self._info_label.configure(text=f'Error connecting to baseband board\n{e}')
                return

            self._baseband = baseband
            info = (f'Hardware version: {info["hw_version"]}\n'
                    f'FPGA version: {info["fpga_version"]}\n'
                    f'Firmware version: {info["sw_version"]}{" (bootloader, no image!)" if info["sw_version"] == "0.0" else ""}')
            self._info_label.configure(text=info)

            self._settings = self._baseband.read_settings()
            self._update_controls()
            self._timer = self.after(BASEBAND_UPDATE_RATE, self._baseband_tasks)

    def _baseband_tasks(self):
        self._check_for_changes()
        self._update_vu_meters()
        self._timer = self.after(BASEBAND_UPDATE_RATE, self._baseband_tasks)

    def _update_controls(self):
        '''
        Update the controls on all dialogs from the settings object.
        '''
        for dialog in self._all_dialogs:
            if dialog is not None and dialog.winfo_exists():
                dialog.update_controls(self._settings)

    def _check_for_changes(self):
        '''
        Update the settings object from the controls on all dialogs.
        '''
        if self._baseband is not None:
            is_dirty = False
            for dialog in self._all_dialogs:
                if dialog is not None and dialog.winfo_exists():
                    if dialog.is_dirty:
                        dialog.clear_dirty()
                        is_dirty = True
            if self._settings is not None and is_dirty:
                self._update_controls()
                self._update_baseband()
            is_dirty = False

    def _update_baseband(self):
        if self._baseband is not None and self._settings is not None:
            self._baseband.write_settings(self._settings)

    def _update_vu_meters(self):
        if self._baseband is not None:
            actuals = self._baseband.read_actuals()
            self._video_meter.set((actuals.adc_in_max - actuals.adc_in_min) / 1024)
            self._nicam_meter_l.set(to_log(actuals.adc1_left_audio_peak / PEAK_FS))
            self._nicam_meter_r.set(to_log(actuals.adc1_right_audio_peak / PEAK_FS))
            for i in range(NR_FM_CARRIERS):
                fm_level = getattr(actuals, f'fm{i+1}_audio_peak') / FM_PEAK_FS
                self._fm_meter[i].set(to_log(fm_level))

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

    def _load_preset(self):
        if self._baseband is not None and self._settings is not None:
            msg = CTkMessagebox(title="Exit?", message="Are you sure to overwrite the current settings?",
                        icon="question", option_1="Cancel", option_2="Yes")
            if msg.get() == "Yes":
                if self._selected_preset.get() == FLAT_WITH_OSD:
                    self._settings.fm[0].enable = 0
                    self._settings.fm[1].enable = 0
                    self._settings.fm[2].enable = 0
                    self._settings.fm[3].enable = 0
                    self._settings.nicam.enable = 0
                    self._settings.video.video_level = 128
                    self._settings.video.video_mode = 0
                    self._settings.video.show_menu = 1
                    self._settings.video.enable = 1
                    self._settings.video.video_in = 1
                    self._update_baseband()
                elif self._selected_preset.get() == SET_DEFAULTS:
                    self._baseband.set_default()
                    self._settings = self._baseband.read_settings()
                self._update_controls()

if __name__ == '__main__':
    gui = Gui()
    gui.mainloop()

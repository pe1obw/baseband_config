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

PEAK_VIDEO_IN = 1023
ADC_FS = 32768
PEAK_FS = 32768
NICAM_PEAK_FS = 1024
FM_PEAK_FS = 2048 * 0.75  # TODO! Is this correct?
ADC_MIN_DB = -40
NICAM_MIN_DB = -40
FM_MIN_DB = -40
BASEBAND_UPDATE_RATE = 100  # in ms

SET_DEFAULTS = 'Set defaults'
FLAT_WITH_OSD = 'Flat with OSD'


def to_log(value: float, min: float = -80) -> float:
    """
    for inputs between 0 and 1, convert to dB and scale to 0 (-80dBFS) to 1 (0dBFS)
    """
    if value == 0.0:
        return 0
    vu = max(0, (20 * math.log10(value) / -min) + 1)
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


class VuMeter(customtkinter.CTkFrame):
    def __init__(self, master, width=200, stereo=False, **kwargs):
        super().__init__(master, width=width, height=25 if stereo else 15, **kwargs)
        self._stereo = stereo
        self._geo = None

    def place(self, x, y):
        super().place(x=x, y=y)
        self.update()
        self._update_dimensions()

    def _draw_background(self):
        # remove all
        self._canvas.delete('all')

        # Add vertical lines from begin to end, at regular intervals
        nr_lines = 9
        for i in range(nr_lines):
            x = 3 + i * (self._width - 3) // (nr_lines - 1)
            self._canvas.create_line(x, 0, x, self._height, fill='grey', width=2)

        if self._stereo:
            self._rec_bg_l = self._canvas.create_rectangle(0, self._y1, self._width, self._y2, fill='darkgreen')
            self._rec_bg_r = self._canvas.create_rectangle(0, self._y3, self._width, self._y4, fill='darkgreen')
            self._rec_idx_l = self._canvas.create_rectangle(0, self._y1, 0, self._y2, fill='lightgreen')
            self._rec_idx_r = self._canvas.create_rectangle(0, self._y3, 0, self._y4, fill='lightgreen')
        else:
            self._rec_bg = self._canvas.create_rectangle(0, self._y1, self._width, self._y4, fill='darkgreen')
            self._rec_idx = self._canvas.create_rectangle(0, self._y1, 0, self._y4, fill='lightgreen')

    def _update_dimensions(self):
        geo = self.winfo_geometry()
        if geo != self._geo:
            self._geo = geo
            self._width, self._height = [int(x) for x in geo.split('+')[0].split('x')]  # width, height
            self._y1 = self._height / 5
            self._y2 = 2 * (self._height / 5)
            self._y3 = 3 * (self._height / 5)
            self._y4 = 4 * (self._height / 5)
            self._draw_background()

    def set(self, value_max: float, value_min: float = 0.0):
        '''
        Set the progress bar
        '''
        self._update_dimensions()

        # assure a minimum bar length
        value_max = max(value_max, value_min + 0.03)

        color = 'lightgreen' if value_min >= 0 and value_max < 1.0 else 'red'
        self._canvas.coords(self._rec_idx, self._width * value_min, self._y1, self._width * value_max, self._y4)
        self._canvas.itemconfig(self._rec_idx, fill=color)

    def set_stereo(self, left: float, right: float):
        '''
        Set the progress bar for stereo
        '''
        self._update_dimensions()
        # assure a minimum bar length
        left = max(left, 0.03)
        right = max(right, 0.03)

        l_color = 'lightgreen' if left < 1.0 else 'red'
        r_color = 'lightgreen' if right < 1.0 else 'red'
        self._canvas.coords(self._rec_idx_l, 0, self._y1, self._width * left, self._y2)
        self._canvas.coords(self._rec_idx_r, 0, self._y3, self._width * right, self._y4)
        self._canvas.itemconfig(self._rec_idx_l, fill=l_color)
        self._canvas.itemconfig(self._rec_idx_r, fill=r_color)

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
        self._is_dirty = False
        self._construct_main_dialog()

    @property
    def _all_dialogs(self):
        return [self._video_dialog, self._nicam_dialog, self._generator_dialog] + self._fm_dialog

    def _construct_main_dialog(self):
        WINDOW_WIDTH = 560
        WINDOW_HEIGHT = 570
        VU_WIDTH = 180
        YPAD = 2
        BUTTON_WIDTH = 15
        SETTING_TEXT = 'Setup'
        ROW_DISTANCE = 35
        COL2 = 100
        COL3 = 300
        MARGIN = 10
        FRAME_TITLE_COLOR = 'grey30'

        # dark theme
        customtkinter.set_appearance_mode("dark")
        self.title('Baseband settings')
        self.geometry(f'{WINDOW_WIDTH}x{WINDOW_HEIGHT}')
        self.resizable(False, False)
        row = 10

        # Connections
        frame_height = 50
        self._frame = customtkinter.CTkFrame(self, height=frame_height, width=WINDOW_WIDTH-2*MARGIN)
        self._frame.place(x=MARGIN, y=row)
        frow = MARGIN
        row += frame_height + MARGIN

        self._settings_button = customtkinter.CTkButton(self._frame, text='Interface', width=BUTTON_WIDTH, command=self._settings_dialog)
        self._settings_button.place(x=MARGIN, y=frow)
        self._connect_button = customtkinter.CTkButton(self._frame, text='Connect', width=BUTTON_WIDTH, command=self._connect)
        self._connect_button.place(x=MARGIN+COL2, y=frow)
        self._info_label = customtkinter.CTkLabel(self._frame, text='Not connected\n \n ')
        self._info_label.place(x=MARGIN+COL3, y=frow)

        # Inputs
        frame_height = 370
        frame_width = WINDOW_WIDTH - 2*MARGIN
        frow = MARGIN
        self._frame = customtkinter.CTkFrame(self, height=frame_height, width=frame_width)
        self._frame.place(x=MARGIN, y=row)
        row += frame_height + MARGIN

        self._frame_title = customtkinter.CTkLabel(self._frame, fg_color=FRAME_TITLE_COLOR, corner_radius=6, text=' Inputs', width=frame_width-2*MARGIN)
        self._frame_title.place(x=MARGIN, y=frow)
        frow += ROW_DISTANCE

        self._adc1_label = customtkinter.CTkLabel(self._frame, text='ADC 1')
        self._adc1_label.place(x=MARGIN, y=frow)
        self._adc1_meter = VuMeter(self._frame, width=VU_WIDTH, stereo=True)
        self._adc1_meter.place(x=MARGIN+COL2, y=frow)
        self._meter1_select_i2s = customtkinter.CTkCheckBox(self._frame, text='I2S', command=self._change_checkbox)
        self._meter1_select_i2s.place(x=MARGIN+COL3, y=frow)
        frow += ROW_DISTANCE

        self._adc2_label = customtkinter.CTkLabel(self._frame, text='ADC 2')
        self._adc2_label.place(x=MARGIN, y=frow)
        self._adc2_meter = VuMeter(self._frame, width=VU_WIDTH, stereo=True)
        self._adc2_meter.place(x=MARGIN+COL2, y=frow)
        self._meter2_select_i2s = customtkinter.CTkCheckBox(self._frame, text='I2S', command=self._change_checkbox)
        self._meter2_select_i2s.place(x=MARGIN+COL3, y=frow)
        frow += ROW_DISTANCE

        self._video_label = customtkinter.CTkLabel(self._frame, text='Video')
        self._video_label.place(x=MARGIN, y=frow)
        self._video_meter = VuMeter(self._frame, width=VU_WIDTH)
        self._video_meter.place(x=MARGIN+COL2, y=frow+5)
        self._video_meter.set(0.4, 0.5)
        self._video_settings = customtkinter.CTkButton(self._frame, text=SETTING_TEXT, command=self._video_settings_dialog, width=BUTTON_WIDTH)
        self._video_settings.place(x=MARGIN+COL3, y=frow)
        frow += ROW_DISTANCE

        self._nicam_label = customtkinter.CTkLabel(self._frame, text='NICAM')
        self._nicam_label.place(x=MARGIN, y=frow)
        self._nicam_meter = VuMeter(self._frame, width=VU_WIDTH, stereo=True)
        self._nicam_meter.place(x=MARGIN+COL2, y=frow)
        self._nicam_settings = customtkinter.CTkButton(self._frame, text=SETTING_TEXT, command=self._nicam_settings_dialog, width=BUTTON_WIDTH)
        self._nicam_settings.place(x=MARGIN+COL3, y=frow)
        frow += ROW_DISTANCE

        self._fm_label = []
        self._fm_meter = []
        self._fm_settings = []
        for i in range(NR_FM_CARRIERS):
            self._fm_label.append(customtkinter.CTkLabel(self._frame, text=f'FM {i+1}'))
            self._fm_label[i].place(x=MARGIN, y=frow)
            self._fm_meter.append(VuMeter(self._frame, width=VU_WIDTH))
            self._fm_meter[i].place(x=MARGIN+COL2, y=frow+5)
            self._fm_meter[i].set(0.1 * i)
            self._fm_settings.append(customtkinter.CTkButton(self._frame, text=SETTING_TEXT, command=lambda i=i: self._fm_settings_dialog(i),
                                                             width=BUTTON_WIDTH))
            self._fm_settings[i].place(x=MARGIN+COL3, y=frow)
            frow += ROW_DISTANCE

        self._audio_generator_label = customtkinter.CTkLabel(self._frame, text='Audio generator')
        self._audio_generator_label.place(x=MARGIN, y=frow)
        self._audio_generator_settings = customtkinter.CTkButton(self._frame, text=SETTING_TEXT, command=self._generator_settings_dialog, width=BUTTON_WIDTH)
        self._audio_generator_settings.place(x=MARGIN+COL3, y=frow)

        # Presets
        frame_height = 100
        self._frame = customtkinter.CTkFrame(self, height=frame_height, width=WINDOW_WIDTH-2*MARGIN)
        self._frame.place(x=MARGIN, y=row)
        row += frame_height + MARGIN
        frow = MARGIN

        self._frame_title = customtkinter.CTkLabel(self._frame, text='Presets', fg_color=FRAME_TITLE_COLOR, corner_radius=6, width=frame_width-2*MARGIN)
        self._frame_title.place(x=MARGIN, y=frow)
        frow += ROW_DISTANCE

        presets = [SET_DEFAULTS, FLAT_WITH_OSD]
        self._load_preset_label = customtkinter.CTkLabel(self._frame, text='Preset')
        self._load_preset_label.place(x=MARGIN, y=frow)
        self._selected_preset = customtkinter.CTkComboBox(self._frame, width=VU_WIDTH - 30, values=presets, state='readonly')
        self._selected_preset.place(x=MARGIN+COL2, y=frow)
        self._selected_preset.set(presets[0])
        self._load_preset_button = customtkinter.CTkButton(self._frame, text='Load', width=BUTTON_WIDTH, command=self._load_preset)
        self._load_preset_button.place(x=MARGIN+COL3, y=frow)

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
            info = (f'Firmware version: {info["sw_version"]}{" (bootloader, no image!)" if info["sw_version"] == "0.0" else ""}\n'
                    f'Hardware version: {info["hw_version"]}, FPGA version: {info["fpga_version"]}')
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
        if self._settings is None:
            return
        for dialog in self._all_dialogs:
            if dialog is not None and dialog.winfo_exists():
                dialog.update_controls(self._settings)
            self._meter1_select_i2s.select() if self._settings.general.peak1_input_i2s_select else self._meter1_select_i2s.deselect()
            self._meter2_select_i2s.select() if self._settings.general.peak2_input_i2s_select else self._meter2_select_i2s.deselect()

    def _check_for_changes(self):
        '''
        Update the settings object from the controls on all dialogs.
        '''
        if self._baseband is not None:
            is_dirty = self._is_dirty
            for dialog in self._all_dialogs:
                if dialog is not None and dialog.winfo_exists():
                    if dialog.is_dirty:
                        dialog.clear_dirty()
                        is_dirty = True
            if self._settings is not None and is_dirty:
                self._update_controls()
                self._update_baseband()
            is_dirty = False
            self._is_dirty = False

    def _update_baseband(self):
        if self._baseband is not None and self._settings is not None:
            self._baseband.write_settings(self._settings)

    def _update_vu_meters(self):
        if self._baseband is not None:
            actuals = self._baseband.read_actuals()
            self._adc1_meter.set_stereo(to_log(actuals.adc1_left_audio_peak / ADC_FS, ADC_MIN_DB),
                                        to_log(actuals.adc1_right_audio_peak / ADC_FS, ADC_MIN_DB))
            self._adc2_meter.set_stereo(to_log(actuals.adc2_left_audio_peak / ADC_FS, ADC_MIN_DB),
                                        to_log(actuals.adc2_right_audio_peak / ADC_FS, ADC_MIN_DB))
            self._video_meter.set(actuals.adc_in_min / PEAK_VIDEO_IN, actuals.adc_in_max / PEAK_VIDEO_IN)
            self._nicam_meter.set_stereo(to_log(actuals.nicam_left_peak / NICAM_PEAK_FS, NICAM_MIN_DB),
                                         to_log(actuals.nicam_right_peak / NICAM_PEAK_FS, NICAM_MIN_DB))
            for i in range(NR_FM_CARRIERS):
                fm_level = getattr(actuals, f'fm{i+1}_audio_peak') / FM_PEAK_FS
                self._fm_meter[i].set(to_log(fm_level, FM_MIN_DB))

    def _change_checkbox(self):
        if self._settings is None:
            return
        self._settings.general.peak1_input_i2s_select = self._meter1_select_i2s.get()
        self._settings.general.peak2_input_i2s_select = self._meter2_select_i2s.get()
        self._is_dirty = True

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

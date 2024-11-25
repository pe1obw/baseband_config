"""
Simple GUI for configuring the baseband board

(C) 2024 PE1OBW, PE1MUD
"""
from typing import Optional
import customtkinter

from baseband.settings import SETTINGS

video_mode_names = ['Flat', 'PAL', 'NTSC', 'SECAM']
osd_mode_names = ['Off', 'On', 'Auto']
video_input_names = ['Video in', 'Video generator', 'Auto']
pattern_names = ['None', 'Color bars', 'Crosshatch', 'Checkerboard', 'Color ramp', 'Color bars 75%']
max_video_level = 255


class VideoDialog(customtkinter.CTkToplevel):
    """
    FM dialog for configuring a single FM/AM carrier.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._settings = None
        self._is_dirty = False
        self._create_widgets()

    @property
    def is_dirty(self):
        return self._is_dirty

    def clear_dirty(self):
        self._is_dirty = False

    def _create_widgets(self):
        pady = 5
        row = 0

        self.geometry("550x400")
        # self.resizable(False, False)
        self.title(f'Video settings')

        self._video_enable_label = customtkinter.CTkLabel(self, text='Video')
        self._video_enable_label.grid(row=row, column=0, padx=20, pady=pady, sticky='w')
        self._video_enable = customtkinter.CTkCheckBox(self, text='Enable', command=self._change_checkbox)
        self._video_enable.grid(row=row, column=1, padx=20, pady=pady, sticky='w')

        row += 1
        self._video_input_label = customtkinter.CTkLabel(self, text='Video input select')
        self._video_input_label.grid(row=row, column=0, padx=20, pady=pady, sticky='w')
        self._video_input = customtkinter.CTkComboBox(self, values=video_input_names, command=self._change_combo, state='readonly')
        self._video_input.grid(row=row, column=1, padx=20, pady=pady, sticky='w')

        row += 1
        self._mode_label = customtkinter.CTkLabel(self, text='Video mode')
        self._mode_label.grid(row=row, column=0, padx=20, pady=pady, sticky='w')
        self._mode = customtkinter.CTkComboBox(self, values=video_mode_names, command=self._change_combo, state='readonly')
        self._mode.grid(row=row, column=1, padx=20, pady=pady, sticky='w')

        row += 1
        self._osd_mode_label = customtkinter.CTkLabel(self, text='OSD mode')
        self._osd_mode_label.grid(row=row, column=0, padx=20, pady=pady, sticky='w')
        self._osd_mode = customtkinter.CTkComboBox(self, values=osd_mode_names, command=self._change_combo, state='readonly')
        self._osd_mode.grid(row=row, column=1, padx=20, pady=pady, sticky='w')

        row += 1
        self._osd_menu_label = customtkinter.CTkLabel(self, text='Show OSD menu')
        self._osd_menu_label.grid(row=row, column=0, padx=20, pady=pady, sticky='w')
        self._osd_menu = customtkinter.CTkCheckBox(self, text='Enable', command=self._change_checkbox)
        self._osd_menu.grid(row=row, column=1, padx=20, pady=pady, sticky='w')

        row += 1
        self._pattern_label = customtkinter.CTkLabel(self, text='Pattern')
        self._pattern_label.grid(row=row, column=0, padx=20, pady=pady, sticky='w')
        self._pattern = customtkinter.CTkComboBox(self, values=pattern_names, command=self._change_combo, state='readonly')
        self._pattern.grid(row=row, column=1, padx=20, pady=pady, sticky='w')
        self._pattern_enable = customtkinter.CTkCheckBox(self, text='Enable', command=self._change_checkbox)
        self._pattern_enable.grid(row=row, column=2, padx=20, pady=pady, sticky='w')

        row += 1
        self._video_level_label = customtkinter.CTkLabel(self, text='Video level')
        self._video_level_label.grid(row=row, column=0, padx=20, pady=pady, sticky='w')
        self._video_level_slider = customtkinter.CTkSlider(self, from_=0, to=max_video_level, orientation='horizontal', command=self._change_slider)
        self._video_level_slider.grid(row=row, column=1, padx=20, pady=pady, sticky='w')
        self._video_level = customtkinter.CTkEntry(self, width=50)
        self._video_level.bind('<Return>', self._change_text)
        self._video_level.bind('<FocusOut>', self._change_text)
        self._video_level.grid(row=row, column=2, padx=20, pady=pady, sticky='w')

        row += 1
        self._video_invert_label = customtkinter.CTkLabel(self, text='Video invert')
        self._video_invert_label.grid(row=row, column=0, padx=20, pady=pady, sticky='w')
        self._video_invert = customtkinter.CTkCheckBox(self, text='Invert', command=self._change_checkbox)
        self._video_invert.grid(row=row, column=1, padx=20, pady=pady, sticky='w')

        row += 1
        self._video_filter_bypass_label = customtkinter.CTkLabel(self, text='Video filter bypass')
        self._video_filter_bypass_label.grid(row=row, column=0, padx=20, pady=pady, sticky='w')
        self._video_filter_bypass = customtkinter.CTkCheckBox(self, text='Bypass', command=self._change_checkbox)
        self._video_filter_bypass.grid(row=row, column=1, padx=20, pady=pady, sticky='w')

    def _change_checkbox(self):
        if self._settings is None:
            return
        self._settings.video.enable = self._video_enable.get()
        self._settings.video.show_menu = self._osd_menu.get()
        self._settings.video.pattern_enable = self._pattern_enable.get()
        self._settings.video.invert_video = self._video_invert.get()
        self._settings.video.filter_bypass = self._video_filter_bypass.get()
        self._is_dirty = True

    def _change_text(self, event):
        if self._settings is None:
            return
        if self._video_level.get() != '':
            self._settings.video.video_level = int(self._video_level.get())
        self._is_dirty = True

    def _change_slider(self, event):
        if self._settings is None:
            return
        self._settings.video.video_level = int(self._video_level_slider.get())
        self._is_dirty = True

    def _change_combo(self, event):
        if self._settings is None:
            return
        self._settings.video.video_in = video_input_names.index(self._video_input.get())
        self._settings.video.video_mode = video_mode_names.index(self._mode.get())
        self._settings.video.osd_mode = osd_mode_names.index(self._osd_mode.get())
        # self._settings.video.pattern = pattern_names.index(self._pattern.get())
        self._is_dirty = True

    def update_controls(self, settings: Optional[SETTINGS]):
        """
        Update all controls from the settings object.
        """
        if settings is None:
            return  # No settings available
        self._settings = settings

        self._video_enable.select() if settings.video.enable else self._video_enable.deselect()
        self._osd_menu.select() if settings.video.show_menu else self._osd_menu.deselect()
        self._pattern_enable.select() if settings.video.pattern_enable else self._pattern_enable.deselect()
        self._video_invert.select() if settings.video.invert_video else self._video_invert.deselect()
        self._video_filter_bypass.select() if settings.video.filter_bypass else self._video_filter_bypass.deselect()

        self._video_input.set(video_input_names[settings.video.video_in])
        self._mode.set(video_mode_names[settings.video.video_mode])
        self._osd_mode.set(osd_mode_names[settings.video.osd_mode])
        # self._pattern.set(pattern_names[settings.video.pattern])

        self._video_level_slider.set(settings.video.video_level)
        self._video_level.delete(0, 'end')
        self._video_level.insert(0, settings.video.video_level)

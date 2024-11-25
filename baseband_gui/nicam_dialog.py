"""
Simple GUI for configuring the baseband board

(C) 2024 PE1OBW, PE1MUD
"""
from typing import Optional
import customtkinter

from baseband.settings import SETTINGS

input_names = ['ADC1L', 'ADC1R', 'ADC2L', 'ADC2R', 'I2S1L', 'I2S1R', 'I2S2L', 'I2S2R', 'ADC1LR', 'ADC2LR', 'I2S1LR', 'I2S2LR', 'MUTE']
bandwidth_names = ['700', '500']
generator_levels = ['0dB', '-6dB', '-12dB', '-18dB', '-24dB', '-30dB', '-36dB', '-42dB', '-48dB', '-54dB', '-60dB', '-66dB', '-72dB', '-78dB', '-84dB', '-90dB']
max_nicam_level = 1023


class NicamDialog(customtkinter.CTkToplevel):
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
        self.title('NICAM settings')

        self._nicam_enable_label = customtkinter.CTkLabel(self, text='Nicam carrier')
        self._nicam_enable_label.grid(row=row, column=0, padx=20, pady=pady, sticky='w')
        self._nicam_enable = customtkinter.CTkCheckBox(self, text='Enable', command=self._change_checkbox)
        self._nicam_enable.grid(row=row, column=1, padx=20, pady=pady, sticky='w')

        row += 1
        self._input_ch1_label = customtkinter.CTkLabel(self, text='Input channel 1')
        self._input_ch1_label.grid(row=row, column=0, padx=20, pady=pady, sticky='w')
        self._input_ch1 = customtkinter.CTkComboBox(self, values=input_names, command=self._change_combo, state='readonly')
        self._input_ch1.grid(row=row, column=1, padx=20, pady=pady, sticky='w')

        row += 1
        self._input_ch2_label = customtkinter.CTkLabel(self, text='Input channel 2')
        self._input_ch2_label.grid(row=row, column=0, padx=20, pady=pady, sticky='w')
        self._input_ch2 = customtkinter.CTkComboBox(self, values=input_names, command=self._change_combo, state='readonly')
        self._input_ch2.grid(row=row, column=1, padx=20, pady=pady, sticky='w')

        row += 1
        self._generator_level_ch1_label = customtkinter.CTkLabel(self, text='Channel 1 generator level')
        self._generator_level_ch1_label.grid(row=row, column=0, padx=20, pady=pady, sticky='w')
        self._generator_level_ch1 = customtkinter.CTkComboBox(self, values=generator_levels, command=self._change_combo, state='readonly')
        self._generator_level_ch1.grid(row=row, column=1, padx=20, pady=pady, sticky='w')
        self._generator_enable_ch1 = customtkinter.CTkCheckBox(self, text='Enable', command=self._change_checkbox)
        self._generator_enable_ch1.grid(row=row, column=2, padx=20, pady=pady, sticky='w')

        row += 1
        self._generator_level_ch2_label = customtkinter.CTkLabel(self, text='Channel 2 generator level')
        self._generator_level_ch2_label.grid(row=row, column=0, padx=20, pady=pady, sticky='w')
        self._generator_level_ch2 = customtkinter.CTkComboBox(self, values=generator_levels, command=self._change_combo, state='readonly')
        self._generator_level_ch2.grid(row=row, column=1, padx=20, pady=pady, sticky='w')
        self._generator_enable_ch2 = customtkinter.CTkCheckBox(self, text='Enable', command=self._change_checkbox)
        self._generator_enable_ch2.grid(row=row, column=2, padx=20, pady=pady, sticky='w')

        row += 1
        self._nicam_frequency_label = customtkinter.CTkLabel(self, text='Frequency (kHz)')
        self._nicam_frequency_label.grid(row=row, column=0, padx=20, pady=pady, sticky='w')
        self._nicam_frequency_slider = customtkinter.CTkSlider(self, from_=0, to=10000, orientation='horizontal', command=self._change_slider)
        self._nicam_frequency_slider.grid(row=row, column=1, padx=20, pady=pady, sticky='w')
        self._nicam_frequency = customtkinter.CTkEntry(self, width=50)
        self._nicam_frequency.bind('<Return>', self._change_text)
        self._nicam_frequency.bind('<FocusOut>', self._change_text)
        self._nicam_frequency.grid(row=row, column=2, padx=20, pady=pady, sticky='w')

        row += 1
        self._nicam_bandwidth_label = customtkinter.CTkLabel(self, text='Bandwidth (kHz)')
        self._nicam_bandwidth_label.grid(row=row, column=0, padx=20, pady=pady, sticky='w')
        self._nicam_bandwidth = customtkinter.CTkComboBox(self, values=['700', '500'], command=self._change_combo, state='readonly')
        self._nicam_bandwidth.grid(row=row, column=1, padx=20, pady=pady, sticky='w')

        row += 1
        self._nicam_level_label = customtkinter.CTkLabel(self, text='RF level')
        self._nicam_level_label.grid(row=row, column=0, padx=20, pady=pady, sticky='w')
        self._nicam_level_slider = customtkinter.CTkSlider(self, from_=0, to=max_nicam_level, orientation='horizontal', command=self._change_slider)
        self._nicam_level_slider.grid(row=row, column=1, padx=20, pady=pady)
        self._nicam_level = customtkinter.CTkEntry(self, width=50)
        self._nicam_level.bind('<Return>', self._change_text)
        self._nicam_level.grid(row=row, column=2, padx=20, pady=pady, sticky='w')

        row += 1
        self._nicam_invert_spectrum_label = customtkinter.CTkLabel(self, text='Invert spectrum')
        self._nicam_invert_spectrum_label.grid(row=row, column=0, padx=20, pady=pady, sticky='w')
        self._nicam_invert_spectrum = customtkinter.CTkCheckBox(self, text='Invert')
        self._nicam_invert_spectrum.grid(row=row, column=1, padx=20, pady=pady, sticky='w')

    def _change_checkbox(self):
        if self._settings is None:
            return
        self._settings.nicam.enable = self._nicam_enable.get()
        self._settings.nicam.invert_spectrum = self._nicam_invert_spectrum.get()
        self._settings.nicam.generator_ena_ch1 = self._generator_enable_ch1.get()
        self._settings.nicam.generator_ena_ch2 = self._generator_enable_ch2.get()
        self._is_dirty = True

    def _change_text(self, event):
        print(f'event: {event}')
        if self._settings is None:
            return
        if self._nicam_frequency.get() != '':
            self._settings.nicam.rf_frequency_khz = int(self._nicam_frequency.get())
        if self._nicam_level.get() != '':
            self._settings.nicam.rf_level = int(self._nicam_level.get())
        self._is_dirty = True

    def _change_slider(self, event):
        if self._settings is None:
            return
        self._settings.nicam.rf_frequency_khz = int(self._nicam_frequency_slider.get())
        self._settings.nicam.rf_level = int(self._nicam_level_slider.get())
        self._is_dirty = True

    def _change_combo(self, event):
        if self._settings is None:
            return
        self._settings.nicam.input_ch1 = input_names.index(self._input_ch1.get())
        self._settings.nicam.input_ch2 = input_names.index(self._input_ch2.get())
        self._settings.nicam.generator_level_ch1 = generator_levels.index(self._generator_level_ch1.get())
        self._settings.nicam.generator_level_ch2 = generator_levels.index(self._generator_level_ch2.get())
        self._settings.nicam.nicam_bandwidth = bandwidth_names.index(self._nicam_bandwidth.get())
        self._is_dirty = True

    def update_controls(self, settings: Optional[SETTINGS]):
        """
        Update all controls from the settings object.
        """
        if settings is None:
            return  # No settings available
        self._settings = settings

        self._nicam_enable.select() if settings.nicam.enable else self._nicam_enable.deselect()
        self._input_ch1.set(input_names[settings.nicam.input_ch1])
        self._input_ch2.set(input_names[settings.nicam.input_ch2])
        self._generator_level_ch1.set(generator_levels[settings.nicam.generator_level_ch1])
        self._generator_enable_ch1.select() if settings.nicam.generator_ena_ch1 else self._generator_enable_ch1.deselect()
        self._generator_level_ch2.set(generator_levels[settings.nicam.generator_level_ch2])
        self._generator_enable_ch2.select() if settings.nicam.generator_ena_ch2 else self._generator_enable_ch2.deselect()
        self._nicam_frequency_slider.set(settings.nicam.rf_frequency_khz)
        self._nicam_frequency.delete(0, 'end')
        self._nicam_frequency.insert(0, settings.nicam.rf_frequency_khz)
        self._nicam_bandwidth.set(bandwidth_names[settings.nicam.nicam_bandwidth])
        self._nicam_level_slider.set(settings.nicam.rf_level)
        self._nicam_level.delete(0, 'end')
        self._nicam_level.insert(0, settings.nicam.rf_level)

        self._nicam_invert_spectrum.select() if settings.nicam.invert_spectrum else self._nicam_invert_spectrum.deselect()

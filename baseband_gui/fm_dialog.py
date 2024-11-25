"""
Simple GUI for configuring the baseband board

(C) 2024 PE1OBW, PE1MUD
"""
from typing import Optional
import customtkinter

from baseband.settings import SETTINGS

input_names = ['ADC1L', 'ADC1R', 'ADC2L', 'ADC2R', 'I2S1L', 'I2S1R', 'I2S2L', 'I2S2R', 'ADC1LR', 'ADC2LR', 'I2S1LR', 'I2S2LR', 'MUTE']
generator_levels = ['0dB', '-6dB', '-12dB', '-18dB', '-24dB', '-30dB', '-36dB', '-42dB', '-48dB', '-54dB', '-60dB', '-66dB', '-72dB', '-78dB', '-84dB', '-90dB']
preemphasis_names = ['50us', '75us', 'J17', 'Flat']
bandwidth_names = ['130', '180', '230', '280']
modulation_names = ['FM', 'AM']
max_carrier_level = 1023


class FmDialog(customtkinter.CTkToplevel):
    """
    FM dialog for configuring a single FM/AM carrier.
    """
    def __init__(self, *args, carrier_index: int, **kwargs):
        super().__init__(*args, **kwargs)
        self._settings = None
        self._idx = carrier_index
        self._nr = carrier_index + 1
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
        self.title(f'FM {self._nr} settings')

        self._fm_enable_label = customtkinter.CTkLabel(self, text='Analog carrier')
        self._fm_enable_label.grid(row=row, column=0, padx=20, pady=pady, sticky='w')
        self._fm_enable = customtkinter.CTkCheckBox(self, text='Enable', command=self._change_checkbox)
        self._fm_enable.grid(row=row, column=1, padx=20, pady=pady, sticky='w')

        row += 1
        self._input_label = customtkinter.CTkLabel(self, text='Audio input')
        self._input_label.grid(row=row, column=0, padx=20, pady=pady, sticky='w')
        self._input = customtkinter.CTkComboBox(self, values=input_names, command=self._change_combo, state='readonly')
        self._input.grid(row=row, column=1, padx=20, pady=pady, sticky='w')

        row += 1
        self._generator_level_label = customtkinter.CTkLabel(self, text='Audio generator level')
        self._generator_level_label.grid(row=row, column=0, padx=20, pady=pady, sticky='w')
        self._generator_level = customtkinter.CTkComboBox(self, values=generator_levels, command=self._change_combo, state='readonly')
        self._generator_level.grid(row=row, column=1, padx=20, pady=pady, sticky='w')
        self._generator_enable = customtkinter.CTkCheckBox(self, text='Enable', command=self._change_checkbox)
        self._generator_enable.grid(row=row, column=2, padx=20, pady=pady, sticky='w')

        self._modulation_label = customtkinter.CTkLabel(self, text='Modulation')
        self._modulation = customtkinter.CTkComboBox(self, values=modulation_names, command=self._change_combo, state='readonly')
        if 0 <= self._idx <= 1:
            row += 1
            self._modulation_label.grid(row=row, column=0, padx=20, pady=pady, sticky='w')
            self._modulation.grid(row=row, column=1, padx=20, pady=pady, sticky='w')

        row += 1
        self._preemphasis_label = customtkinter.CTkLabel(self, text='Preemphasis')
        self._preemphasis_label.grid(row=row, column=0, padx=20, pady=pady, sticky='w')
        self._preemphasis = customtkinter.CTkComboBox(self, values=preemphasis_names, command=self._change_combo, state='readonly')
        self._preemphasis.grid(row=row, column=1, padx=20, pady=pady, sticky='w')

        row += 1
        self._bandwidth_label = customtkinter.CTkLabel(self, text='RF bandwidth (kHz)')
        self._bandwidth_label.grid(row=row, column=0, padx=20, pady=pady, sticky='w')
        self._bandwidth = customtkinter.CTkComboBox(self, values=bandwidth_names, command=self._change_combo, state='readonly')
        self._bandwidth.grid(row=row, column=1, padx=20, pady=pady, sticky='w')

        row += 1
        self._frequency_label = customtkinter.CTkLabel(self, text='Frequency (kHz)')
        self._frequency_label.grid(row=row, column=0, padx=20, pady=pady, sticky='w')
        self._frequency_slider = customtkinter.CTkSlider(self, from_=0, to=10000, orientation='horizontal', command=self._change_slider)
        self._frequency_slider.grid(row=row, column=1, padx=20, pady=pady, sticky='w')
        self._frequency = customtkinter.CTkEntry(self, width=50)
        self._frequency.bind('<Return>', self._change_text)
        self._frequency.bind('<FocusOut>', self._change_text)
        self._frequency.grid(row=row, column=2, padx=20, pady=pady, sticky='w')

        row += 1
        self._rf_level_label = customtkinter.CTkLabel(self, text='RF level')
        self._rf_level_label.grid(row=row, column=0, padx=20, pady=pady, sticky='w')
        self._rf_level_slider = customtkinter.CTkSlider(self, from_=0, to=max_carrier_level, orientation='horizontal', command=self._change_slider)
        self._rf_level_slider.grid(row=row, column=1, padx=20, pady=pady)
        self._rf_level = customtkinter.CTkEntry(self, width=50)
        self._rf_level.bind('<Return>', self._change_text)
        self._rf_level.bind('<FocusOut>', self._change_text)
        self._rf_level.grid(row=row, column=2, padx=20, pady=pady, sticky='w')

    def _change_checkbox(self):
        if self._settings is None:
            return
        self._settings.fm[self._idx].enable = self._fm_enable.get()
        self._settings.fm[self._idx].generator_ena = self._generator_enable.get()
        self._is_dirty = True

    def _change_text(self, event):
        if self._settings is None:
            return
        if self._frequency.get() != '':
            self._settings.fm[self._idx].rf_frequency_khz = int(self._frequency.get())
        if self._rf_level.get() != '':
            self._settings.fm[self._idx].rf_level = int(self._rf_level.get())
        self._is_dirty = True

    def _change_slider(self, event):
        if self._settings is None:
            return
        self._settings.fm[self._idx].rf_frequency_khz = int(self._frequency_slider.get())
        self._settings.fm[self._idx].rf_level = int(self._rf_level_slider.get())
        self._is_dirty = True

    def _change_combo(self, event):
        if self._settings is None:
            return
        self._settings.fm[self._idx].input = input_names.index(self._input.get())
        self._settings.fm[self._idx].generator_level = generator_levels.index(self._generator_level.get())
        self._settings.fm[self._idx].preemphasis = preemphasis_names.index(self._preemphasis.get())
        self._settings.fm[self._idx].fm_bandwidth = bandwidth_names.index(self._bandwidth.get())
        self._settings.fm[self._idx].am = modulation_names.index(self._modulation.get())
        self._is_dirty = True

    def update_controls(self, settings: Optional[SETTINGS]):
        """
        Update all controls from the settings object.
        """
        if settings is None:
            return  # No settings available
        self._settings = settings

        self._fm_enable.select() if settings.fm[self._idx].enable else self._fm_enable.deselect()
        self._input.set(input_names[settings.fm[self._idx].input])
        self._generator_level.set(generator_levels[settings.fm[self._idx].generator_level])
        self._generator_enable.select() if settings.fm[self._idx].generator_ena else self._generator_enable.deselect()
        self._modulation.set(modulation_names[settings.fm[self._idx].am])
        if settings.fm[self._idx].am == 1:
            self._preemphasis.configure(state='disabled')
            self._bandwidth.configure(state='disabled')
        else:
            self._preemphasis.configure(state='normal')
            self._bandwidth.configure(state='normal')
        self._frequency_slider.set(settings.fm[self._idx].rf_frequency_khz)
        self._frequency.delete(0, 'end')
        self._frequency.insert(0, settings.fm[self._idx].rf_frequency_khz)
        self._preemphasis.set(preemphasis_names[settings.fm[self._idx].preemphasis])
        self._bandwidth.set(bandwidth_names[settings.fm[self._idx].fm_bandwidth])
        self._rf_level_slider.set(settings.fm[self._idx].rf_level)
        self._rf_level.delete(0, 'end')
        self._rf_level.insert(0, settings.fm[self._idx].rf_level)

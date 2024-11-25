"""
Simple GUI for configuring the baseband board

(C) 2024 PE1OBW, PE1MUD
"""
import math
from typing import Optional
import customtkinter

from baseband.settings import NR_FM_CARRIERS, SETTINGS

max_generator_frequency = 15000
waveform_names = ['Sine', 'Square', 'Noise']
mode_names = ['CW', 'Morse']
morse_speed_names = ['7.5', '15', '30', '60']
generator_levels = ['0dB', '-6dB', '-12dB', '-18dB', '-24dB', '-30dB', '-36dB', '-42dB', '-48dB', '-54dB', '-60dB', '-66dB', '-72dB', '-78dB', '-84dB', '-90dB']


max_morse_repeat_time = 1023
max_morse_text_length = 16


def freq_to_log(freq: int) -> int:
    """
    Convert frequency to logarithmic scale, return nr between 0 and 1000
    for f = 0 to 15000 Hz
    """
    if freq < 15:
        return 0
    return int(math.log10(freq / 15) * 1000 / 3)


def log_to_freq(log_fr: float) -> int:
    """
    Convert logarithmic scale to frequency
    """
    return int(15 * 10 ** (log_fr / (1000 / 3)))

class GeneratorDialog(customtkinter.CTkToplevel):
    """
    Dialog for configuring the audio generator
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

        self.geometry("650x500")
        # self.resizable(False, False)
        self.title(f'Audio generator settings')

        self._frequency_label = customtkinter.CTkLabel(self, text='Frequency (Hz)')
        self._frequency_label.grid(row=row, column=0, padx=20, pady=pady, sticky='w')
        self._frequency_slider = customtkinter.CTkSlider(self, from_=0, to=1000, orientation='horizontal', command=self._change_slider)
        self._frequency_slider.grid(row=row, column=1, padx=20, pady=pady, sticky='w')
        self._frequency = customtkinter.CTkEntry(self, width=50)
        self._frequency.bind('<Return>', self._change_text)
        self._frequency.bind('<FocusOut>', self._change_text)
        self._frequency.grid(row=row, column=2, padx=20, pady=pady, sticky='w')

        row += 1
        self._waveform_label = customtkinter.CTkLabel(self, text='Waveform select')
        self._waveform_label.grid(row=row, column=0, padx=20, pady=pady, sticky='w')
        self._waveform = customtkinter.CTkComboBox(self, values=waveform_names, command=self._change_combo, state='readonly')
        self._waveform.grid(row=row, column=1, padx=20, pady=pady, sticky='w')

        row += 1
        self._mode_label = customtkinter.CTkLabel(self, text='Generator mode')
        self._mode_label.grid(row=row, column=0, padx=20, pady=pady, sticky='w')
        self._mode = customtkinter.CTkComboBox(self, values=mode_names, command=self._change_combo, state='readonly')
        self._mode.grid(row=row, column=1, padx=20, pady=pady, sticky='w')

        row += 1
        self._morse_text_label = customtkinter.CTkLabel(self, text='Morse text (max 16 characters)')
        self._morse_text_label.grid(row=row, column=0, padx=20, pady=pady, sticky='w')
        self._morse_text = customtkinter.CTkEntry(self, width=200)
        self._morse_text.bind('<Return>', self._change_text)
        self._morse_text.bind('<FocusOut>', self._change_text)
        self._morse_text.grid(row=row, column=1, padx=20, pady=pady, sticky='w', columnspan=2)

        row += 1
        self._morse_speed_label = customtkinter.CTkLabel(self, text='Morse speed (points/min)')
        self._morse_speed_label.grid(row=row, column=0, padx=20, pady=pady, sticky='w')
        self._morse_speed = customtkinter.CTkComboBox(self, values=morse_speed_names, command=self._change_combo, state='readonly')
        self._morse_speed.grid(row=row, column=1, padx=20, pady=pady, sticky='w')

        row += 1
        self._morse_repeat_time_label = customtkinter.CTkLabel(self, text='Message repeat time (s)')
        self._morse_repeat_time_label.grid(row=row, column=0, padx=20, pady=pady, sticky='w')
        self._morse_message_repeat_time_slider = customtkinter.CTkSlider(self, from_=0, to=max_morse_repeat_time, orientation='horizontal', command=self._change_slider)
        self._morse_message_repeat_time_slider.grid(row=row, column=1, padx=20, pady=pady, sticky='w')
        self._morse_message_repeat_time = customtkinter.CTkEntry(self, width=50)
        self._morse_message_repeat_time.bind('<Return>', self._change_text)
        self._morse_message_repeat_time.bind('<FocusOut>', self._change_text)
        self._morse_message_repeat_time.grid(row=row, column=2, padx=20, pady=pady, sticky='w')

        row += 1
        self._generator_level_nicam_ch1_label = customtkinter.CTkLabel(self, text='Nicam channel 1 generator level')
        self._generator_level_nicam_ch1_label.grid(row=row, column=0, padx=20, pady=pady, sticky='w')
        self._generator_level_nicam_ch1 = customtkinter.CTkComboBox(self, values=generator_levels, command=self._change_combo, state='readonly')
        self._generator_level_nicam_ch1.grid(row=row, column=1, padx=20, pady=pady, sticky='w')
        self._generator_enable_nicam_ch1 = customtkinter.CTkCheckBox(self, text='Enable', command=self._change_checkbox)
        self._generator_enable_nicam_ch1.grid(row=row, column=2, padx=20, pady=pady, sticky='w')

        row += 1
        self._generator_level_nicam_ch2_label = customtkinter.CTkLabel(self, text='Nicam channel 2 generator level')
        self._generator_level_nicam_ch2_label.grid(row=row, column=0, padx=20, pady=pady, sticky='w')
        self._generator_level_nicam_ch2 = customtkinter.CTkComboBox(self, values=generator_levels, command=self._change_combo, state='readonly')
        self._generator_level_nicam_ch2.grid(row=row, column=1, padx=20, pady=pady, sticky='w')
        self._generator_enable_nicam_ch2 = customtkinter.CTkCheckBox(self, text='Enable', command=self._change_checkbox)
        self._generator_enable_nicam_ch2.grid(row=row, column=2, padx=20, pady=pady, sticky='w')

        self._fm = []
        for idx in range(NR_FM_CARRIERS):
            row += 1
            generator_level_label = customtkinter.CTkLabel(self, text=f'FM {idx + 1} Audio generator level')
            generator_level_label.grid(row=row, column=0, padx=20, pady=pady, sticky='w')
            generator_level = customtkinter.CTkComboBox(self, values=generator_levels, command=self._change_combo, state='readonly')
            generator_level.grid(row=row, column=1, padx=20, pady=pady, sticky='w')
            generator_enable = customtkinter.CTkCheckBox(self, text='Enable', command=self._change_checkbox)
            generator_enable.grid(row=row, column=2, padx=20, pady=pady, sticky='w')
            self._fm.append((generator_level, generator_enable))

    def _change_checkbox(self):
        if self._settings is None:
            return
        self._settings.general.generator_ena_ch1 = self._generator_enable_nicam_ch1.get()
        self._settings.general.generator_ena_ch2 = self._generator_enable_nicam_ch2.get()
        for idx in range(NR_FM_CARRIERS):
            self._settings.fm[idx].generator_ena = self._fm[idx][1].get()
        self._is_dirty = True

    def _change_text(self, event):
        if self._settings is None:
            return
        if self._frequency.get() != '':
            self._settings.general.audio_nco_frequency = int(self._frequency.get())
        if self._morse_message_repeat_time.get() != '':
            self._settings.general.morse_message_repeat_time = int(self._morse_message_repeat_time.get())
        if self._morse_text.get() != '':
            self._settings.general.morse_message = (self._morse_text.get()[0:max_morse_text_length]).encode('utf-8')
        self._is_dirty = True

    def _change_slider(self, event):
        if self._settings is None:
            return
        self._settings.general.audio_nco_frequency = log_to_freq(self._frequency_slider.get())
        self._settings.general.morse_message_repeat_time = int(self._morse_message_repeat_time_slider.get())
        self._is_dirty = True

    def _change_combo(self, event):
        if self._settings is None:
            return
        self._settings.general.audio_nco_mode = mode_names.index(self._mode.get())
        self._settings.general.morse_speed = morse_speed_names.index(self._morse_speed.get())
        self._settings.general.waveform = waveform_names.index(self._waveform.get())
        self._is_dirty = True

    def update_controls(self, settings: Optional[SETTINGS]):
        """
        Update all controls from the settings object.
        """
        if settings is None:
            return  # No settings available
        self._settings = settings

        self._frequency_slider.set(freq_to_log(settings.general.audio_nco_frequency))
        self._frequency.delete(0, 'end')
        self._frequency.insert(0, settings.general.audio_nco_frequency)

        self._waveform.set(waveform_names[settings.general.audio_nco_waveform])
        self._mode.set(mode_names[settings.general.audio_nco_mode])

        self._morse_speed.set(morse_speed_names[settings.general.morse_speed])
        self._morse_text.delete(0, 'end')
        self._morse_text.insert(0, settings.general.morse_message)
        self._morse_message_repeat_time_slider.set(settings.general.morse_message_repeat_time)
        self._morse_message_repeat_time.delete(0, 'end')
        self._morse_message_repeat_time.insert(0, settings.general.morse_message_repeat_time)

        if settings.general.audio_nco_mode == 1:
            self._morse_speed.configure(state='normal')
            self._morse_text.configure(state='normal')
            self._morse_message_repeat_time_slider.configure(state='normal')
            self._morse_message_repeat_time.configure(state='normal')
        else:
            self._morse_speed.configure(state='disabled')
            self._morse_text.configure(state='disabled')
            self._morse_message_repeat_time_slider.configure(state='disabled')
            self._morse_message_repeat_time.configure(state='disabled')

        self._generator_level_nicam_ch1.set(generator_levels[settings.nicam.generator_level_ch1])
        self._generator_enable_nicam_ch1.select() if settings.nicam.generator_ena_ch1 else self._generator_enable_nicam_ch1.deselect()
        self._generator_level_nicam_ch2.set(generator_levels[settings.nicam.generator_level_ch2])
        self._generator_enable_nicam_ch2.select() if settings.nicam.generator_ena_ch2 else self._generator_enable_nicam_ch2.deselect()
        for idx in range(NR_FM_CARRIERS):
            self._fm[idx][0].set(generator_levels[settings.fm[idx].generator_level])
            self._fm[idx][1].select() if settings.fm[idx].generator_ena else self._fm[idx][1].deselect()

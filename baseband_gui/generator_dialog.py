"""
Simple GUI for configuring the baseband board

(C) 2024 PE1OBW, PE1MUD
"""
from typing import Optional
import customtkinter

from baseband.settings import SETTINGS

max_generator_frequency = 15000
waveform_names = ['Sine', 'Square', 'Noise']
mode_names = ['CW', 'Morse']
morse_speed_names = ['7.5', '15', '30', '60']

max_morse_repeat_time = 1023
max_morse_text_length = 16


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

        self.geometry("550x400")
        # self.resizable(False, False)
        self.title(f'Audio generator settings')

        self._frequency_label = customtkinter.CTkLabel(self, text='Frequency (Hz)')
        self._frequency_label.grid(row=row, column=0, padx=20, pady=pady, sticky='w')
        self._frequency_slider = customtkinter.CTkSlider(self, from_=0, to=max_generator_frequency, orientation='horizontal', command=self._change_slider)
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

    def _change_text(self, event):
        if self._settings is None:
            return
        if self._frequency.get() != '':
            self._settings.general.audio_nco_frequency = int(self._frequency.get())
        if self._morse_message_repeat_time.get() != '':
            self._settings.general.morse_message_repeat_time = int(self._morse_message_repeat_time.get())
        if self._morse_text.get() != '':
            self._settings.general.morse_message = (self._morse_text.get()[0:max_morse_text_length]).encode('utf-8')
        self.update_controls(self._settings)
        self._is_dirty = True

    def _change_slider(self, event):
        if self._settings is None:
            return
        self._settings.general.audio_nco_frequency = int(self._frequency_slider.get())
        self._settings.general.morse_message_repeat_time = int(self._morse_message_repeat_time_slider.get())
        self.update_controls(self._settings)
        self._is_dirty = True

    def _change_combo(self, event):
        if self._settings is None:
            return
        self._settings.general.audio_nco_mode = mode_names.index(self._mode.get())
        self._settings.general.morse_speed = morse_speed_names.index(self._morse_speed.get())
        self._settings.general.waveform = waveform_names.index(self._waveform.get())
        self.update_controls(self._settings)
        self._is_dirty = True

    def update_controls(self, settings: Optional[SETTINGS]):
        """
        Update all controls from the settings object.
        """
        if settings is None:
            return  # No settings available
        self._settings = settings

        self._frequency_slider.set(settings.general.audio_nco_frequency)
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

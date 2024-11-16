from typing import Optional
import customtkinter

from baseband.settings import SETTINGS

input_names = ['ADC1L', 'ADC1R', 'ADC2L', 'ADC2R', 'I2S1L', 'I2S1R', 'I2S2L', 'I2S2R', 'ADC1LR', 'ADC2LR', 'I2S1LR', 'I2S2LR', 'MUTE']


class NicamDialog(customtkinter.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._settings = None

        self.geometry("600x500")

        row = 0

        self.label = customtkinter.CTkLabel(self, text="Nicam settings")
        self.label.grid(row=row, column=0, padx=20, pady=5, columnspan=3)

        dialog = self

        row += 1
        self._nicam_enable_label = customtkinter.CTkLabel(dialog, text='Nicam carrier')
        self._nicam_enable_label.grid(row=row, column=0, padx=20, pady=5, sticky='w')
        self._nicam_enable = customtkinter.CTkCheckBox(dialog, text='Enable', command=self._change_settings)
        self._nicam_enable.grid(row=row, column=1, padx=20, pady=5, sticky='w')

        row += 1
        self._input_ch1_label = customtkinter.CTkLabel(dialog, text='Input channel 1')
        self._input_ch1_label.grid(row=row, column=0, padx=20, pady=5, sticky='w')
        self._input_ch1 = customtkinter.CTkComboBox(dialog, values=input_names, command=self._change_combo, state='readonly')
        self._input_ch1.grid(row=row, column=1, padx=20, pady=5, sticky='w')

        row += 1
        self._input_ch2_label = customtkinter.CTkLabel(dialog, text='Input channel 2')
        self._input_ch2_label.grid(row=row, column=0, padx=20, pady=5, sticky='w')
        self._input_ch2 = customtkinter.CTkComboBox(dialog, values=input_names, command=self._change_combo, state='readonly')
        self._input_ch2.grid(row=row, column=1, padx=20, pady=5, sticky='w')

        row += 1
        self._nicam_frequency_label = customtkinter.CTkLabel(dialog, text='Frequency (MHz)')
        self._nicam_frequency_label.grid(row=row, column=0, padx=20, pady=5)
        self._nicam_frequency_slider = customtkinter.CTkSlider(dialog, from_=0, to=10000, orientation='horizontal', command=self._change_slider)
        self._nicam_frequency_slider.grid(row=row, column=1, padx=20, pady=5, sticky='w')
        self._nicam_frequency = customtkinter.CTkEntry(dialog, width=50)
        self._nicam_frequency.bind('<Return>', self._change_text)
        self._nicam_frequency.grid(row=row, column=2, padx=20, pady=5)

        row += 1
        self._nicam_bandwidth_label = customtkinter.CTkLabel(dialog, text='Bandwidth (kHz)')
        self._nicam_bandwidth_label.grid(row=row, column=0, padx=20, pady=5, sticky='w')
        self._nicam_bandwidth_slider = customtkinter.CTkSlider(dialog, from_=0, to=10000, orientation='horizontal', command=self._change_slider)
        self._nicam_bandwidth_slider.grid(row=row, column=1, padx=20, pady=5)
        self._nicam_bandwidth = customtkinter.CTkEntry(dialog, width=50)
        self._nicam_bandwidth.bind('<Return>', self._change_text)
        self._nicam_bandwidth.grid(row=row, column=2, padx=20, pady=5)

        row += 1
        self._nicam_level_label = customtkinter.CTkLabel(dialog, text='RF level (dBm)')
        self._nicam_level_label.grid(row=row, column=0, padx=20, pady=5, sticky='w')
        self._nicam_level_slider = customtkinter.CTkSlider(dialog, from_=0, to=10000, orientation='horizontal', command=self._change_slider)
        self._nicam_level_slider.grid(row=row, column=1, padx=20, pady=5)
        self._nicam_level = customtkinter.CTkEntry(dialog, width=50)
        self._nicam_level.bind('<Return>', self._change_text)
        self._nicam_level.grid(row=row, column=2, padx=20, pady=5)

        row += 1
        self._nicam_invert_spectrum_label = customtkinter.CTkLabel(dialog, text='Invert spectrum')
        self._nicam_invert_spectrum_label.grid(row=row, column=0, padx=20, pady=5, sticky='w')
        self._nicam_invert_spectrum = customtkinter.CTkCheckBox(dialog, text='Invert')
        self._nicam_invert_spectrum.grid(row=row, column=1, padx=20, pady=5, sticky='w')

    def _change_settings(self):
        if self._settings is None:
            return
        self._settings.nicam.enable = self._nicam_enable.get()
        self._settings.nicam.invert_spectrum = self._nicam_invert_spectrum.get()
        self.update_settings(self._settings)

    def _change_text(self, event):
        print(f'event: {event}')
        if self._settings is None:
            return
        if self._nicam_frequency.get() != '':
            self._settings.nicam.rf_frequency_khz = int(self._nicam_frequency.get())
        # if self._nicam_bandwidth.get() != '':
        #     self._settings.nicam_bandwidth = self._nicam_bandwidth.get()
        if self._nicam_level.get() != '':
            self._settings.nicam.rf_level = int(self._nicam_level.get())
        self.update_settings(self._settings)

    def _change_slider(self, event):
        if self._settings is None:
            return
        self._settings.nicam.rf_frequency_khz = int(self._nicam_frequency_slider.get())
        # self._settings.nicam_bandwidth = self._nicam_bandwidth_slider.get()
        self._settings.nicam.rf_level = int(self._nicam_level_slider.get())
        self.update_settings(self._settings)

    def _change_combo(self, event):
        if self._settings is None:
            return
        self._settings.nicam.input_ch1 = input_names.index(self._input_ch1.get())
        self._settings.nicam.input_ch2 = input_names.index(self._input_ch2.get())
        self.update_settings(self._settings)

    def update_settings(self, settings: Optional[SETTINGS]):
        """
        Update all controls from the settings object.
        """
        if settings is None:
            return  # No settings available
        self._settings = settings

        if settings.nicam.enable:
            self._nicam_enable.select()
        else:
            self._nicam_enable.deselect()

        self._input_ch1.set(input_names[settings.nicam.input_ch1])
        self._input_ch2.set(input_names[settings.nicam.input_ch2])

        self._nicam_frequency_slider.set(settings.nicam.rf_frequency_khz)
        self._nicam_frequency.delete(0, 'end')
        self._nicam_frequency.insert(0, settings.nicam.rf_frequency_khz)
        # self._nicam_bandwidth_slider.set(settings.nicam.bandwidth)
        # self._nicam_bandwidth.delete(0, 'end')
        # self._nicam_bandwidth.insert(0, settings.nicam.bandwidth)
        self._nicam_level_slider.set(settings.nicam.rf_level)
        self._nicam_level.delete(0, 'end')
        self._nicam_level.insert(0, settings.nicam.rf_level)
        if settings.nicam.invert_spectrum:
            self._nicam_invert_spectrum.select()
        else:
            self._nicam_invert_spectrum.deselect()
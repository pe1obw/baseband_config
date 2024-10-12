"""
USB driver wrapper for FTDI devices using the pyftdi library.

If multiple FTDI devices are found and no serialnr or description is provided,
the user is prompted to select the device to use.
If no FTDI device is found, an exception is raised.

(C) 2024 PE1OBW, PE1MUD
"""
import time
from typing import Optional
from pyftdi.usbtools import UsbTools
from pyftdi.i2c import I2cController


class UsbFtdi:
    """
    USB interface for the FTDI device.
    """
    I2C_FREQUENCY = 50000  # Increasing this results in read errors, due to a bug in the FT232H driver/HW. See <https://github.com/eblot/pyftdi/issues/373>
    BB_SLAVE_ADDR = 0xB0//2

    def __init__(self, serial: Optional[str] = None, description : Optional[str] = None):
        self._device = self._get_device(serial, description)
        self._i2c = I2cController()
        self._i2c.configure(self._device, clockstretching=True, frequency=self.I2C_FREQUENCY)  # type: ignore
        self._slave = self._i2c.get_port(self.BB_SLAVE_ADDR)
        # Set the FT232H read latency a bit lower.
        # See <https://ftdichip.com/Support/Documents/AppNotes/AN232B-04_DataLatencyFlow.pdf> for details.
        # Latency is in ms, and can be 1..255 ms. For some reason, 4 ms is the lowest value that works.
        # Below this, the SDA line gets stuck?!
        ftdi = self._i2c.ftdi
        ftdi.set_latency_timer(4)

    def _get_device(self, serial: Optional[str] = None, description: Optional[str] = None):
        device_descriptors = UsbTools().find_all([(0x0403, 0x6014)])
        if not device_descriptors:
            raise Exception('No FTDI device found')

        if serial or description:
            for dev in device_descriptors:
                if serial and dev[0].sn == serial or description and dev[0].description:
                    print(f'Using device {dev}')
                    device_descriptor = dev[0]
                    return UsbTools().get_device(device_descriptor)
            raise Exception('No FTDI device found with the specified serial or description')

        if len(device_descriptors) == 1:
            print(f'Using device: {device_descriptors[0][0]}')
            device_descriptor = device_descriptors[0][0]
        else:
            print('Multiple FTDI devices found, select one:')
            for i, dev in enumerate(device_descriptors):
                print(f'{i}: {dev}')
            i = int(input())
            device_descriptor = device_descriptors[i][0]
            print(f'Selected device: {device_descriptor}')
        return UsbTools().get_device(device_descriptor)

    def write(self, data: bytes):
        self._slave.write(data)

    def read(self, length: int) -> bytes:
        return self._slave.read(length)

    def exchange(self, data: bytes, length: int) -> bytes:
        return self._slave.exchange(data, length)

    def pulse_gpio(self, gpio_nr: int, seconds: float):
        assert gpio_nr > 2 and gpio_nr < 7, f'Invalid GPIO number for FT232H {gpio_nr}'
        gpio = self._i2c.get_gpio()
        gpio.set_direction(pins=1 << gpio_nr, direction=1 << gpio_nr)  # GPIO 6 as output
        gpio.write(0)
        time.sleep(seconds)
        gpio.write(1 << gpio_nr)

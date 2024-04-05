"""
This file contains the code to get the USB device descriptor for the FTDI device.
The device descriptor is used to communicate with the FTDI device.
If multiple FTDI devices are found, the user is prompted to select the device to use.
If no FTDI device is found, an exception is raised.

(C) 2024 PE1OBW, PE1MUD
"""
from typing import Optional
from pyftdi.usbtools import UsbTools, UsbDevice


def get_device(serial: Optional[str] = None, description : Optional[str] = None) -> UsbDevice:
    """
    Try to connect to the FTDI device and return the device descriptor
    """
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

# Baseband control tool for Windows/Linux

THe PE1MUD/PE1OBW Digital Baseband is a hardware device to produce a baseband
signal for analog FM television as used by radio amateurs.
The baseband has an i2c interface which can be used to fully control it.
More information about the baseband can be found on <https://fm-atv.nl>.

This tool controls the baseband using a FTDI FT232H USB<->I2C interface.
The software consists of two parts, a library `Baseband` and an example
application `baseband_config` to demonstrate it. `Baseband_config` is a
command-line program that supports export and import of the baseband settings,
read out of actual audio and video levels, upgrading the firmware and more.

## Installation

You need a Baseband board and an FTDI FT232H interface.
Connect the USB interface to the I2C header (4-pole) on the baseband PCB:

|FT232H   |Baseband |
|---------|---------|
|GND      |GND      |
|AD0      |SCL      |
|AD1      |SDA      |
|AD2      |SDA      |
|AD7      |SCL      |

To protect the FPGA, you could add resistors of e.g., 220 ohms in series
with SCL and SDA. Leave the +5V on the Baseband unconnected! The baseband
uses clock stretching, therefore both the AD0 and the AD7 line must be
connected to SCL.

The FT232H has a few GPIO pins that can be used together with the i2c
functionality. The code contains a command to pulse the AD6 pin (active low),
for example to reset the board remotely.

The FT232H is the only supported FTDI chip that offers true open drain outputs,
but other FTDI devices might be used as well (using diodes).

See <https://eblot.github.io/pyftdi/installation.html> for more information
about the supported USB interfaces and how to connect/install.

Then install the software:

- For Windows only: install the 'Zadig' tool, and replace the existing driver
with `libusb-win32` (see the pyftdi documentation).
- Install the tool with `pip install -e .` (the `-e` option installs the
project in 'editable' mode)
- Run the tool with `baseband_config [options]`

Examples:

```bash
baseband_config --help
```

```bash
baseband_config --info
```

```bash
baseband_config --settings_to_file settings.json`
```

This creates a file with the settings, stored as json.
This file can be modified and its content can be written back to the baseband using:

```bash
baseband_config --settings_from_file settings.json
```

To update the firmware and reboot:

```bash
baseband_config --upgrade baseband_0.26.bin
baseband_config --reboot
```

## Issues

The used FT232H interface, in combination with the PyFTDI library, does not
(fully) support clock stretching. I posted an issue on their web site, maybe
they find a workaround. Until then, only a low speed (50 kbps) can be used.
For read back of the flash, an even lower speed is needed, therefore it is not
supported in the current library.

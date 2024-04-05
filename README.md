# I2c config tool for Windows/Linux

This tool controls the Baseband using a FTDI FT232H USB<->I2C interface.
It consists of a class `Baseband` and an example `baseband_config` to
demonstrate the capabilities.
The `Baseband_config` is a command line program that supports export and
import of the configuration, firmware upgrade and other features.

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
with SCL and SDA. Leave the +5V on the Baseband unconnected. The baseband
uses clock stretching, therefore both the AD0 and the AD7 line must be
connected to SCL.

The FT232H has a few GPIO pins that can be used together with the i2c
functionality. The code contains a command to pulse the AD6 pin (active low),
for example to reset the board remotely.

The FT232H is the only supported FTDI chip that offers true open drain outputs,
but other FTDI devices might be used as well (using diodes).

See <https://eblot.github.io/pyftdi/installation.html> for more information
about the supported USB interfaces and how to connect/install.

See <https://fm-atv.nl> for more information about the Baseband project.

Then install the software:

- For Windows only: install the 'Zadig' tool, and replace the existing driver
with `libusb-win32` (see the pyftdi documentation).
- Install the tool with `pip install -e .` (the `-e` option installs the project in 'editable' mode)
- Run the tool with `baseband_config [options]`

Use `baseband_config --help` to see the available commands.
Examples:

```bash
baseband_config --info
```

Connect to the board and dump a lot of info.

```bash
baseband_config --settings_to_file settings.json`
```

creates a file with the settings, stored as json.
This file can be modified and written back to the baseband using:

```bash
baseband_config --settings_from_file settings.json
```

To update the firmware and reboot:

```bash
baseband_config --upgrade baseband_0.26.bin
baseband_config --reboot
```

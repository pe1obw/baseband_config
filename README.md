# Baseband control tool for Windows/Linux

THe PE1MUD/PE1OBW Digital Baseband is a hardware device to produce a baseband
signal for analog FM television as used by radio amateurs.
The baseband has an i2c interface which can be used to fully control it.
More information about the baseband can be found on <https://fm-atv.nl>.

This tool controls the baseband from a PC using a USB<->I2C interface.
Currently, interface with the following chips are supported:

- The FTDI FT232H (others might work, but have no open drain output)
- The MCP2221A

Both have issues. The FT232H does not support clock stretching, making it
unusable for some commands. The FT232H is the only supported FTDI chip
that offers true open drain outputs, but other FTDI devices might be used
as well (using diodes). See <https://eblot.github.io/pyftdi/installation.html>
for more information about the supported USB interfaces and how to connect
and install.

The CP2221A does support clock stretching, but the drivers have issues.The
software supports two MCP2221A Python drivers: EasyMCP2221 and PyMCP2221A.
EasyMCP2221A works best, but shows very long delays between commands on one of
my PCs. PyMCP2221A has multiple problems and is not recommended as it does not
support firmware upgrade yet and is known to leave the i2c bus in a hang state.

The software consists of two parts, a library `baseband` and an example
application `baseband_config`.
`Baseband_config` is a command-line program that supports export and import
of the baseband settings, read out of actual audio and video levels, upgrading
the firmware and more.

Both the FT232H and the MCP2221A have a few GPIO pins that can be used together
with the i2c functionality. The code contains a command to pulse a GPIO pin
(active low), for example to reset the board remotely. For the FT232H, gpio's
3...6 are available, on the MCP2221A you can use GPIO0..3. On the MCP, however,
the GPIOs seem to have predefined functions; I see GPIO0 pulsing at 50 Hz when
connecting to the USB port...

## Installation

You need a Baseband board and a supported USB <-> I2C interface.
Connect the USB interface to the I2C header (4-pole) on the baseband PCB. For
the FT232H, wiring is as shown below:

|FT232H   |Baseband |
|---------|---------|
|GND      |GND      |
|AD0      |SCL      |
|AD1      |SDA      |
|AD2      |SDA      |
|AD7      |SCL      |

The baseband uses clock stretching, therefore both the AD0 and the AD7 line
must be connected to SCL.

For the MCP2221A, wiring is straightforward: connect SDA, SCL and GND to the
respective pins on the 4-pole Baseband I2C header.

To protect the FPGA, you could add resistors of e.g., 220 ohms in series
with SCL and SDA. Leave the +5V on the Baseband unconnected!

Then install the software:

- For Windows and the FT232H only: install the 'Zadig' tool, and replace
the existing driver with `libusb-win32` (see the pyftdi documentation).
- Install the tool with `pip install -e .` (the `-e` option installs the
project in 'editable' mode)
- Run the tool with `baseband_config [options]`

Examples (replace `--usb_ftdi` by `--usb_easymcp` for the MCP2221A chip):

Show all options

```bash
baseband_config --help
```

Use MCP2221 chip, show baseband info (version and actual settings)

```bash
baseband_config --usb_ftdi --info
```

To create a file with the settings, stored as json:

```bash
baseband_config --usb_ftdi --settings_to_file settings.json`
```

The settings file can be modified and its contents can be written back.
It is also possible to write back a partial json (i.e., only these settings
will be modified).
To write back to the baseband:

```bash
baseband_config --usb_ftdi --settings_from_file settings.json
```

To update the firmware and reboot when done:

```bash
baseband_config --usb_ftdi --upgrade baseband_0.26.bin
baseband_config --usb_ftdi --reboot
```

Change some settings:

```bash
baseband_config --usb_ftdi --set fm.0.rf_frequency_khz=7020
baseband_config --usb_ftdi --set video.video_level=100
baseband_config --usb_ftdi --set video.video_mode=PAL
baseband_config --usb_ftdi --set "name=23cm TX"
```

See the `settings.py` file for the possible fields in the settings string.

To store the actual settings to preset 10:

```bash
baseband_config --usb_ftdi --store_preset=10
```

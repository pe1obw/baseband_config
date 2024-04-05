"""
(C) 2024 PE1OBW, PE1MUD
"""
from pyftdi.i2c import I2cPort


def dump_osd_memory(slave: I2cPort) -> None:
    """
    Read & print actual OSD contents
    """
    for y in range(0, 16):
        addr = 0x00 + y*40
        result = slave.exchange([addr >> 8, addr & 255], 40)
        for i in range(0, len(result)):
            print (f'{result[i]:02X}', end=' ')
        print('  [', end='')
        for i in range(0, len(result)):
            char = result[i] if result[i] >= 32 and result[i] < 127 else 32
            print (f'{chr(char)}', end='')
        print(']')

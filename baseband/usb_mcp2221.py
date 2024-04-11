"""
USB interface for the MCP2221A USB to I2C bridge.

FIXME: The PyMCP2221A library has issues:
- Read fails with more than a few bytes.
- Write fails with more than ~60 bytes.
- On failure, the bus gets stuck and does not recover.
"""
from typing import Optional
from PyMCP2221A import PyMCP2221A


class UsbMcp2221:
    SLAVE_ADDR = 0xB0 // 2

    def __init__(self, serial: Optional[str] = None, description : Optional[str] = None):
        self.mcp = PyMCP2221A.PyMCP2221A()
        self.mcp.I2C_Init(speed=100000)

    def write(self, data: bytes):
        self.mcp.I2C_Write(self.SLAVE_ADDR, data)

    def read(self, length: int) -> bytes:
        return bytes(self.mcp.I2C_Read(self.SLAVE_ADDR, length))

    def exchange(self, data: bytes, length: int) -> bytes:
        # For now: write_non_stop and read_repeated do not work with > 12..30 bytes
        # (depeding on PC!), hence this fix.
        self.mcp.I2C_Write(self.SLAVE_ADDR, data)
        result: bytes = []
        while length > 0:
            readlen = min(length, 12)
            data = self.mcp.I2C_Read(self.SLAVE_ADDR, readlen)
            assert data != -1, 'I2C read error'
            result.extend(data)
            length -= readlen
        return bytes(result)

    def pulse_gpio(self, gpio_nr: int, seconds: float):
        raise NotImplementedError('Pulse GPIO is not supported (yet) with MCP2221A lib')

"""
USB interface for the MCP2221A USB to I2C bridge.
"""
import time
from typing import Optional
import EasyMCP2221

class UsbEasyMcp:
    SLAVE_ADDR = 0xB0 // 2

    def __init__(self, serial: Optional[str] = None, description : Optional[str] = None):
        self.mcp = EasyMCP2221.Device()
        self.mcp.I2C_speed(400000)

    def write(self, data: bytes):
        self.mcp.I2C_write(self.SLAVE_ADDR, data, timeout_ms=500)

    def read(self, length: int) -> bytes:
        return bytes(self.mcp.I2C_read(self.SLAVE_ADDR, length, timeout_ms=500))

    def exchange(self, data: bytes, length: int) -> bytes:
        self.mcp.I2C_write(self.SLAVE_ADDR, data, kind='nonstop', timeout_ms=500)
        result = self.mcp.I2C_read(self.SLAVE_ADDR, length, kind='restart', timeout_ms=500)
        return bytes(result)

    def pulse_gpio(self, gpio_nr: int, seconds: float):
        raise NotImplementedError('Pulse GPIO is not supported (yet) with MCP2221A')

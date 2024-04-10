"""
USB interface for the MCP2221A USB to I2C bridge.
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
        print(f'REad {length} bytes after writing {len(data)} bytes')
        self.mcp.I2C_Write_No_Stop(self.SLAVE_ADDR, data)
        result = self.mcp.I2C_Read_Repeated(self.SLAVE_ADDR, length)
        assert result != -1, 'I2C read error'
        return bytes(result)

    def pulse_gpio(self, gpio_nr: int, seconds: float):
        raise NotImplementedError('Pulse GPIO is not supported (yet) with MCP2221A')

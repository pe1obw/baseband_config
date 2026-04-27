"""
USB interface for the MCP2221A USB to I2C bridge.
"""
import time
import EasyMCP2221

class UsbEasyMcp:
    SLAVE_ADDR = 0xB0 // 2
    # SLAVE_ADDR = 0x64

    def __init__(self, slave_addr : int = SLAVE_ADDR):
        self.slave_addr = slave_addr
        self.mcp = EasyMCP2221.Device()
        self.mcp.I2C_speed(400000)

    def write(self, data: bytes):
        self.mcp.I2C_write(self.slave_addr, data, timeout_ms=500)

    def read(self, length: int) -> bytes:
        return bytes(self.mcp.I2C_read(self.slave_addr, length, timeout_ms=500))

    def exchange(self, data: bytes, length: int) -> bytes:
        self.mcp.I2C_write(self.slave_addr, data, kind='nonstop', timeout_ms=500)
        result = self.mcp.I2C_read(self.slave_addr, length, kind='restart', timeout_ms=500)
        return bytes(result)

    def pulse_gpio(self, gpio_nr: int, seconds: float):
        assert seconds > 0, 'Pulse time must be > 0'
        assert gpio_nr >= 0 and gpio_nr <= 3, 'Invalid GPIO number, must be 0..3 for MCP2221A'
        params = {0: 'gp0', 1: 'gp1', 2: 'gp2', 3: 'gp3'}
        self.mcp.set_pin_function(**{params[gpio_nr]: "GPIO_OUT"})  # type: ignore
        self.mcp.GPIO_write(**{params[gpio_nr]: False})
        time.sleep(seconds)
        self.mcp.GPIO_write(**{params[gpio_nr]: True})

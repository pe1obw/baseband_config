"""
Firmware configuration for the baseband board.

(C) 2024 PE1OBW, PE1MUD
"""
from typing import Optional

I2C_ACCESS_FLASH = 0x7000  # R/W maps to flash SPI interface

# Flash memory layout
FLASH_SIZE          = 0x100000
FLASH_UPGRADE_START = 0x080000
FLASH_UPGRADE_END   = 0x0FFFFF
FLASH_SECTOR_SIZE   = 0x010000
FLASH_PAGE_SIZE     = 256

# M25P80 commands
WRITE_ENABLE = 0x06
WRITE_DISABLE = 0x04
READ_IDENTIFICATION = 0x9F
READ_STATUS_REGISTER = 0x05
WRITE_STATUS_REGISTER = 0x01
READ_DATA_BYTES = 0x03
PAGE_PROGRAM = 0x02
SECTOR_ERASE = 0xD8
BULK_ERASE = 0xC7

# M25P80 status register bits
WRITE_IN_PROGRESS = 1

MIN_FIRMWARE_SIZE = 400000


class FirmwareControl:
    """
    This class is responsible for flashing the firmware to the baseband board
    """
    def __init__(self, slave):
        self._slave = slave

    def get_flash_id(self) -> bytearray:
        """
        Read manufacturer and device ID from the flash memory
        """
        return self._m25p80_command(READ_IDENTIFICATION, None, bytearray(), 3)

    def flash_firmware(self, firmware: bytes) -> None:
        """
        Flash firmware to the baseband board
        """
        assert len(firmware) > MIN_FIRMWARE_SIZE and len(firmware) < FLASH_UPGRADE_END - FLASH_UPGRADE_START, f'Firmware size mismatch'
        self._flash_erase(FLASH_UPGRADE_START, FLASH_UPGRADE_END)
        self._flash_write(FLASH_UPGRADE_START, firmware)

        print('Firmware flashed')

    def read_firmware(self) -> bytes:
        """
        Read firmware from the baseband board
        """
        READ_BLOCK_SIZE = 1024
        firmware = bytearray()
        for addr in range(FLASH_UPGRADE_START, FLASH_UPGRADE_END, READ_BLOCK_SIZE):
            data = self._m25p80_command(READ_DATA_BYTES, addr, bytearray(), READ_BLOCK_SIZE)
            firmware += data
            if addr & 0xFFFF == 0:  # 64 kB progress
                progress = 100 * (addr - FLASH_UPGRADE_START) / (FLASH_UPGRADE_END-FLASH_UPGRADE_START)
                print(f'reading firmware from 0x{addr:06X} ({progress:.1f}%)')

        return bytes(firmware)

    def _flash_erase(self, start, end):
        """
        Erase a flash memory region
        """
        print(f'Erasing flash from 0x{start:06X} to 0x{end:06X}')
        for addr in range(start, end, FLASH_SECTOR_SIZE):
            self._erase_sector(addr)

    def _erase_sector(self, sector_address: int):
        print(f'Erase sector at 0x{sector_address & ~(FLASH_SECTOR_SIZE-1):06X}')
        self._m25p80_command(WRITE_ENABLE, None, bytearray())
        self._m25p80_command(SECTOR_ERASE, sector_address, bytearray())
        while True:
            status = self._m25p80_command(READ_STATUS_REGISTER, None, bytearray(), 1)
            if not status[0] & WRITE_IN_PROGRESS:
                break

    def _flash_write(self, start: int, data: bytes):
        """
        Write data to a flash memory region
        """
        addr = start
        end = addr + len(data)
        print(f'Writing flash from 0x{start:06X} to 0x{end:06X}')
        while addr < end:
            if addr & 0x3FFF == 0:  # 64 kB progress
                progress = 100 * (addr - start) / len(data)
                print(f'writing firmware to 0x{addr:06X} ({progress:.1f}%)')
            page_size = min(FLASH_PAGE_SIZE, end - addr)
            self._write_page(addr, data[addr-start:addr-start+page_size])
            addr += page_size

    def _write_page(self, page_address: int, data: bytes):
        self._m25p80_command(WRITE_ENABLE, None, bytearray())
        self._m25p80_command(PAGE_PROGRAM, page_address, data)
        while True:
            status = self._m25p80_command(READ_STATUS_REGISTER, None, bytearray(), 1)
            if not status[0] & WRITE_IN_PROGRESS:
                break

    def _m25p80_command(self, command: int, flash_address: Optional[int], outdata: bytes, nr_to_read: int = 0) -> bytearray:
        """
        Issue a command to the M25P80 flash memory.
        The Baseband acts as a SPI master to the flash memory.
        """
        assert command != BULK_ERASE, 'Bulk erase not allowed'
        if flash_address:
            assert flash_address < FLASH_SIZE and flash_address >= 0, 'Address out of range'
            assert not ((command == PAGE_PROGRAM or command == SECTOR_ERASE) and
                        (flash_address < FLASH_UPGRADE_START or flash_address > FLASH_UPGRADE_END)), 'write/erase not allowed outside upgrade region'

        extra = 3 if command == READ_DATA_BYTES or command == PAGE_PROGRAM or command == SECTOR_ERASE else 0
        num_bytes_to_transfer = 1 + extra + len(outdata) + nr_to_read
        address = (I2C_ACCESS_FLASH + num_bytes_to_transfer)
        header = bytearray([(address >> 8) & 255, address & 255, command])
        if flash_address:
            header += bytearray([(flash_address >> 16) & 255, (flash_address >> 8) & 255, flash_address & 255])

        result = bytearray()
        if nr_to_read:
            result = self._slave.exchange(header, nr_to_read)
        else:
            self._slave.write(header + outdata)
        return result

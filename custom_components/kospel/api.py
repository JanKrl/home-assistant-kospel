"""API client for Kospel Electric Heaters using Modbus TCP."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException
from homeassistant.exceptions import HomeAssistantError

_LOGGER = logging.getLogger(__name__)


class KospelAPIError(HomeAssistantError):
    """Exception to indicate a general API error."""


class KospelConnectionError(KospelAPIError):
    """Exception to indicate a connection error."""


class KospelAuthError(KospelAPIError):
    """Exception to indicate an authentication error."""


class KospelAPI:
    """API client for Kospel electric heaters using Modbus TCP."""

    # Modbus register addresses for Kospel C.MI
    # These addresses are based on common heating system implementations
    # and may need adjustment based on actual Kospel documentation
    REGISTERS = {
        # Status registers (holding registers for reading)
        "current_temperature": 0x0001,      # Current room temperature (°C * 10)
        "target_temperature": 0x0002,       # Target temperature (°C * 10)
        "heater_status": 0x0003,            # Heater on/off status (0/1)
        "operating_mode": 0x0004,           # Operating mode (0=off, 1=heat, 2=auto, 3=eco)
        "water_heating_status": 0x0005,     # Water heating status (0/1)
        "water_target_temp": 0x0006,        # Water target temperature (°C * 10)
        "power_consumption": 0x0007,        # Current power consumption (W)
        "error_code": 0x0008,               # Error code (0 = no error)
        
        # Control registers (holding registers for writing)
        "set_target_temp": 0x0102,          # Set target temperature (°C * 10)
        "set_mode": 0x0103,                 # Set operating mode
        "set_heater_on": 0x0104,            # Turn heater on/off
        "set_water_temp": 0x0105,           # Set water temperature (°C * 10)
    }

    def __init__(
        self,
        host: str,
        port: int = 502,
        slave_id: int = 1,
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        """Initialize the API client."""
        self._host = host
        self._port = port
        self._slave_id = slave_id
        self._username = username
        self._password = password
        self._client = AsyncModbusTcpClient(host=host, port=port)

    async def test_connection(self) -> bool:
        """Test connection to the device."""
        try:
            await self._client.connect()
            if not self._client.connected:
                raise KospelConnectionError("Unable to connect to Modbus device")
            
            # Try to read a basic register to verify communication
            result = await self._client.read_holding_registers(
                self.REGISTERS["current_temperature"], 
                1, 
                slave=self._slave_id
            )
            
            if result.isError():
                raise KospelConnectionError(f"Modbus communication error: {result}")
            
            await self._client.close()
            return True
        except Exception as exc:
            _LOGGER.error("Connection test failed: %s", exc)
            raise KospelConnectionError("Unable to connect to device") from exc

    async def get_status(self) -> dict[str, Any]:
        """Get current status from the heater."""
        try:
            await self._ensure_connected()
            
            # Read all status registers in one call for efficiency
            result = await self._client.read_holding_registers(
                self.REGISTERS["current_temperature"], 
                8,  # Read 8 consecutive registers
                slave=self._slave_id
            )
            
            if result.isError():
                raise KospelAPIError(f"Failed to read status registers: {result}")
            
            registers = result.registers
            
            return {
                "current_temperature": registers[0] / 10.0,  # Convert from °C * 10
                "target_temperature": registers[1] / 10.0,
                "heater_running": bool(registers[2]),
                "mode": self._decode_mode(registers[3]),
                "water_heating": bool(registers[4]),
                "water_temperature": registers[5] / 10.0,
                "power": registers[6],
                "error_code": registers[7],
                "last_update": asyncio.get_event_loop().time(),
            }
            
        except ModbusException as exc:
            _LOGGER.error("Modbus error reading status: %s", exc)
            raise KospelAPIError("Failed to get device status") from exc
        except Exception as exc:
            _LOGGER.error("Failed to get status: %s", exc)
            raise KospelAPIError("Failed to get device status") from exc

    async def get_settings(self) -> dict[str, Any]:
        """Get current settings from the heater."""
        try:
            await self._ensure_connected()
            
            # For settings, we return the same data as status for now
            # In a real implementation, there might be additional configuration registers
            status = await self.get_status()
            
            return {
                "target_temperature": status["target_temperature"],
                "mode": status["mode"],
                "water_temperature": status["water_temperature"],
                "last_update": status["last_update"],
            }
            
        except Exception as exc:
            _LOGGER.error("Failed to get settings: %s", exc)
            raise KospelAPIError("Failed to get device settings") from exc

    async def set_temperature(self, temperature: float) -> bool:
        """Set target temperature."""
        try:
            await self._ensure_connected()
            
            # Convert temperature to register value (°C * 10)
            temp_value = int(temperature * 10)
            
            # Clamp to valid range
            temp_value = max(150, min(350, temp_value))  # 15°C to 35°C
            
            result = await self._client.write_register(
                self.REGISTERS["set_target_temp"],
                temp_value,
                slave=self._slave_id
            )
            
            if result.isError():
                raise KospelAPIError(f"Failed to write temperature: {result}")
            
            _LOGGER.debug("Successfully set temperature to %.1f°C", temperature)
            return True
            
        except Exception as exc:
            _LOGGER.error("Failed to set temperature: %s", exc)
            raise KospelAPIError("Failed to set temperature") from exc

    async def set_mode(self, mode: str) -> bool:
        """Set operating mode."""
        try:
            await self._ensure_connected()
            
            mode_value = self._encode_mode(mode)
            
            result = await self._client.write_register(
                self.REGISTERS["set_mode"],
                mode_value,
                slave=self._slave_id
            )
            
            if result.isError():
                raise KospelAPIError(f"Failed to write mode: {result}")
            
            _LOGGER.debug("Successfully set mode to %s", mode)
            return True
            
        except Exception as exc:
            _LOGGER.error("Failed to set mode: %s", exc)
            raise KospelAPIError("Failed to set mode") from exc

    async def set_water_temperature(self, temperature: float) -> bool:
        """Set water heating target temperature."""
        try:
            await self._ensure_connected()
            
            # Convert temperature to register value (°C * 10)
            temp_value = int(temperature * 10)
            
            # Clamp to valid range for water heating
            temp_value = max(200, min(600, temp_value))  # 20°C to 60°C
            
            result = await self._client.write_register(
                self.REGISTERS["set_water_temp"],
                temp_value,
                slave=self._slave_id
            )
            
            if result.isError():
                raise KospelAPIError(f"Failed to write water temperature: {result}")
            
            _LOGGER.debug("Successfully set water temperature to %.1f°C", temperature)
            return True
            
        except Exception as exc:
            _LOGGER.error("Failed to set water temperature: %s", exc)
            raise KospelAPIError("Failed to set water temperature") from exc

    async def _ensure_connected(self) -> None:
        """Ensure the Modbus client is connected."""
        if not self._client.connected:
            await self._client.connect()
            if not self._client.connected:
                raise KospelConnectionError("Failed to connect to Modbus device")

    def _decode_mode(self, mode_value: int) -> str:
        """Decode mode from register value."""
        mode_map = {
            0: "off",
            1: "heat",
            2: "auto", 
            3: "eco",
        }
        return mode_map.get(mode_value, "unknown")

    def _encode_mode(self, mode: str) -> int:
        """Encode mode to register value."""
        mode_map = {
            "off": 0,
            "heat": 1,
            "auto": 2,
            "eco": 3,
        }
        return mode_map.get(mode, 0)

    async def close(self) -> None:
        """Close the Modbus connection."""
        if self._client and self._client.connected:
            await self._client.close()

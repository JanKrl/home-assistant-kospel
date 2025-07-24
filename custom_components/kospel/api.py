"""API client for Kospel Electric Heaters using REST API."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import aiohttp
from homeassistant.exceptions import HomeAssistantError

_LOGGER = logging.getLogger(__name__)


class KospelAPIError(HomeAssistantError):
    """Exception to indicate a general API error."""


class KospelConnectionError(KospelAPIError):
    """Exception to indicate a connection error."""


class KospelAuthError(KospelAPIError):
    """Exception to indicate an authentication error."""


class KospelAPI:
    """API client for Kospel electric heaters using REST API."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        port: int = 80,
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        """Initialize the API client."""
        self._session = session
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._base_url = f"http://{host}:{port}"
        self._device_id = None

    async def test_connection(self) -> bool:
        """Test connection to the device and discover device ID."""
        try:
            # Discover available devices
            await self._discover_device_id()
            
            # Test getting device registers
            await self._get_device_registers()
            
            return True
                
        except (KospelConnectionError, KospelAPIError):
            # Re-raise connection and API errors as-is
            raise
        except Exception as exc:
            _LOGGER.error("Connection test failed: %s", exc)
            raise KospelConnectionError("Unable to connect to device") from exc

    async def get_status(self) -> dict[str, Any]:
        """Get current status from the heater."""
        try:
            # Ensure device ID is discovered before attempting to get registers
            if not self._device_id:
                _LOGGER.debug("Device ID not yet discovered, attempting discovery...")
                await self._discover_device_id()
            
            registers = await self._get_device_registers()
            
            # Parse register values based on the manufacturer's frontend analysis
            # CO = Central heating (Centralne Ogrzewanie)
            # CWU = Water heating (Ciepła Woda Użytkowa)
            # Register mapping analysis based on typical heating system patterns:
            # - Temperature registers typically use 0.1°C resolution
            # - Mode registers use enumerated values
            # - Status registers use bit flags
            
            status_data = {
                # Temperature readings
                "current_temperature": self._parse_temperature(registers.get("0c1c", "0000")),
                "target_temperature_co": self._parse_temperature(registers.get("0bb8", "0000")),  # CO set temp
                "target_temperature_cwu": self._parse_temperature(registers.get("0bb9", "0000")),  # CWU set temp
                "water_temperature": self._parse_temperature(registers.get("0c1d", "0000")),
                "outside_temperature": self._parse_temperature(registers.get("0c1e", "0000")),
                "return_temperature": self._parse_temperature(registers.get("0c1f", "0000")),
                
                # Status indicators
                "heater_running": self._parse_boolean(registers.get("0b30", "0000")),
                "water_heating": self._parse_boolean(registers.get("0b32", "0000")),
                "pump_running": self._parse_boolean(registers.get("0b31", "0000")),
                
                # Operating parameters
                "mode": self._parse_mode(registers.get("0b89", "0000")),
                "power": self._parse_power(registers.get("0c9f", "0000")),
                "error_code": self._parse_error(registers.get("0b62", "0000")),
                
                # Use the CO temperature as the primary target for Home Assistant compatibility
                "target_temperature": self._parse_temperature(registers.get("0bb8", "0000")),
                
                "last_update": asyncio.get_event_loop().time(),
                "raw_registers": registers,  # Include raw data for debugging
            }
            
            _LOGGER.debug("Parsed status data: %s", status_data)
            return status_data
            
        except Exception as exc:
            _LOGGER.error("Failed to get status: %s", exc)
            raise KospelAPIError("Failed to get device status") from exc

    async def get_settings(self) -> dict[str, Any]:
        """Get current settings from the heater."""
        try:
            # Ensure device ID is discovered before attempting to get settings
            if not self._device_id:
                _LOGGER.debug("Device ID not yet discovered, attempting discovery...")
                await self._discover_device_id()
                
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
            # TODO: Implement temperature setting via API
            # This would require discovering the correct endpoint and register
            _LOGGER.warning("Temperature setting not yet implemented - need to discover write endpoints")
            return False
            
        except Exception as exc:
            _LOGGER.error("Failed to set temperature: %s", exc)
            raise KospelAPIError("Failed to set temperature") from exc

    async def set_mode(self, mode: str) -> bool:
        """Set operating mode."""
        try:
            # TODO: Implement mode setting via API
            _LOGGER.warning("Mode setting not yet implemented - need to discover write endpoints")
            return False
            
        except Exception as exc:
            _LOGGER.error("Failed to set mode: %s", exc)
            raise KospelAPIError("Failed to set mode") from exc

    async def _discover_device_id(self) -> None:
        """Discover device ID by querying available devices."""
        try:
            async with asyncio.timeout(10):
                response = await self._session.get(f"{self._base_url}/api/dev")
                
                if response.status >= 400:
                    raise KospelConnectionError(f"HTTP error {response.status}")
                
                data = await response.json()
                
                if data.get("status") != "0":
                    raise KospelConnectionError(f"API error: status {data.get('status')}")
                
                # Get the first device ID
                devs = data.get("devs", [])
                if not devs:
                    raise KospelConnectionError("No devices found")
                
                self._device_id = devs[0]
                _LOGGER.info("Discovered device ID: %s", self._device_id)
                
        except asyncio.TimeoutError as exc:
            _LOGGER.error("Device discovery timeout")
            raise KospelConnectionError("Device discovery timeout") from exc
        except (aiohttp.ClientError, json.JSONDecodeError) as exc:
            _LOGGER.error("Device discovery failed: %s", exc)
            raise KospelConnectionError("Unable to discover device") from exc

    async def _get_device_registers(self) -> dict[str, str]:
        """Get all device registers."""
        if not self._device_id:
            raise KospelAPIError("Device ID not discovered yet")
        
        try:
            async with asyncio.timeout(10):
                response = await self._session.get(
                    f"{self._base_url}/api/dev/{self._device_id}"
                )
                
                if response.status >= 400:
                    raise KospelAPIError(f"HTTP error {response.status}")
                
                data = await response.json()
                
                if data.get("status") != "0":
                    raise KospelAPIError(f"API error: status {data.get('status')}")
                
                registers = data.get("regs", {})
                _LOGGER.debug("Retrieved %d registers", len(registers))
                
                return registers
                
        except asyncio.TimeoutError as exc:
            raise KospelAPIError("Request timeout") from exc
        except (aiohttp.ClientError, json.JSONDecodeError) as exc:
            raise KospelAPIError(f"Request failed: {exc}") from exc

    def _parse_temperature(self, hex_value: str) -> float | None:
        """Parse temperature from hex register value."""
        try:
            # Convert hex to integer
            value = int(hex_value, 16)
            if value == 0xFFFF:  # Invalid/not available
                return None
            
            # Based on register analysis, the pattern is:
            # Little-endian byte order, divided by 10
            # Examples:
            # 4a01 → 0x014a (330) → 33.0°C ✓
            # e001 → 0x01e0 (480) → 48.0°C ✓  
            # 3201 → 0x0132 (306) → 30.6°C ✓
            
            # Convert from little-endian and divide by 10
            little_endian = ((value & 0xFF) << 8) | ((value >> 8) & 0xFF)
            temperature = little_endian / 10.0
            
            _LOGGER.debug("Temperature parsing for %s: LE %d → %.1f°C", hex_value, little_endian, temperature)
            return temperature
            
        except (ValueError, TypeError):
            return None

    def _parse_boolean(self, hex_value: str) -> bool:
        """Parse boolean from hex register value."""
        try:
            value = int(hex_value, 16)
            
            # Based on register analysis, the pattern is:
            # Check if LOW BYTE is non-zero
            # Examples:
            # 0100 (OFF) → low_byte = 0x00 → False ✓
            # 4600 (OFF) → low_byte = 0x00 → False ✓
            # xxxx01 (ON) → low_byte = 0x01 → True ✓
            
            low_byte = value & 0xFF
            result = low_byte != 0
            
            _LOGGER.debug("Boolean parsing for %s: low_byte=%02X → %s", hex_value, low_byte, result)
            return result
            
        except (ValueError, TypeError):
            return False

    def _parse_mode(self, hex_value: str) -> str:
        """Parse operating mode from hex register value."""
        try:
            value = int(hex_value, 16)
            
            # For mode parsing, check both low and high bytes
            low_byte = value & 0xFF
            high_byte = (value >> 8) & 0xFF
            
            _LOGGER.debug("Mode parsing for %s: raw=%d, low_byte=%d, high_byte=%d", 
                         hex_value, value, low_byte, high_byte)
            
            # Common mode mappings for heating systems
            mode_map = {
                0: "off",
                1: "heat",
                2: "auto", 
                3: "eco",
                4: "comfort",
                5: "boost",
                6: "manual",
                # Add common heating system modes
                10: "standby",
                11: "program1",
                12: "program2", 
                13: "program3",
            }
            
            # Try low byte first, then high byte, then full value
            for test_value in [low_byte, high_byte, value]:
                if test_value in mode_map:
                    mode = mode_map[test_value]
                    _LOGGER.debug("Mode result: %s (from value %d)", mode, test_value)
                    return mode
            
            # If no mapping found, return a descriptive value
            mode = f"mode_{value}"
            _LOGGER.debug("Mode result: %s (unmapped)", mode)
            return mode
            
        except (ValueError, TypeError):
            return "unknown"

    def _parse_power(self, hex_value: str) -> int | None:
        """Parse power consumption from hex register value."""
        try:
            value = int(hex_value, 16)
            if value == 0xFFFF:
                return None
            return value
        except (ValueError, TypeError):
            return None

    def _parse_error(self, hex_value: str) -> int:
        """Parse error code from hex register value."""
        try:
            return int(hex_value, 16)
        except (ValueError, TypeError):
            return 0

    async def close(self) -> None:
        """Close the HTTP session."""
        # Session is managed by Home Assistant, don't close it
        pass

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
                _LOGGER.debug("Discovered device ID: %s", self._device_id)
                
                # Test getting device registers
                await self._get_device_registers()
                
                return True
                
        except asyncio.TimeoutError as exc:
            _LOGGER.error("Connection test timeout")
            raise KospelConnectionError("Connection timeout") from exc
        except (aiohttp.ClientError, json.JSONDecodeError) as exc:
            _LOGGER.error("Connection test failed: %s", exc)
            raise KospelConnectionError("Unable to connect to device") from exc

    async def get_status(self) -> dict[str, Any]:
        """Get current status from the heater."""
        try:
            registers = await self._get_device_registers()
            
            # Parse register values based on your actual data
            # These mappings will need to be determined from your register analysis
            status_data = {
                "current_temperature": self._parse_temperature(registers.get("0c1c", "0000")),
                "target_temperature": self._parse_temperature(registers.get("0bb8", "0000")),
                "heater_running": self._parse_boolean(registers.get("0b30", "0000")),
                "mode": self._parse_mode(registers.get("0b89", "0000")),
                "water_heating": self._parse_boolean(registers.get("0b32", "0000")),
                "water_temperature": self._parse_temperature(registers.get("0c1d", "0000")),
                "power": self._parse_power(registers.get("0c9f", "0000")),
                "error_code": self._parse_error(registers.get("0b62", "0000")),
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
            
            # Based on register analysis, these appear to be in 0.01°C units
            # 0c1c = 4a01 (18945) suggests ~189.45°C or likely needs different parsing
            # Let's try different interpretations:
            
            # Method 1: Direct 0.01°C scaling
            temp_method1 = value / 100.0
            
            # Method 2: Check if it's a packed format (high/low bytes)
            high_byte = (value >> 8) & 0xFF
            low_byte = value & 0xFF
            temp_method2 = (high_byte * 256 + low_byte) / 10.0
            
            # Method 3: Assume it's signed 16-bit with different scaling
            if value > 32767:  # Convert from unsigned to signed
                signed_value = value - 65536
            else:
                signed_value = value
            temp_method3 = signed_value / 100.0
            
            # For debugging, log all methods
            _LOGGER.debug(
                "Temperature parsing for %s: raw=%d, method1=%.2f, method2=%.2f, method3=%.2f",
                hex_value, value, temp_method1, temp_method2, temp_method3
            )
            
            # Based on typical room temperatures, choose the most reasonable value
            # For 0c1c=4a01 (18945), method1 gives 189.45°C (too high)
            # Let's try interpreting as little-endian: 0x014a = 330 → 33.0°C
            little_endian = ((value & 0xFF) << 8) | ((value >> 8) & 0xFF)
            temp_little_endian = little_endian / 10.0
            
            _LOGGER.debug("Little endian interpretation: %d → %.1f°C", little_endian, temp_little_endian)
            
            # Return the little-endian interpretation as it gives reasonable values
            return temp_little_endian
            
        except (ValueError, TypeError):
            return None

    def _parse_boolean(self, hex_value: str) -> bool:
        """Parse boolean from hex register value."""
        try:
            value = int(hex_value, 16)
            # Check if this is a packed value where only certain bits matter
            # For 0x0100, this could mean bit 8 is set, indicating "on"
            # For now, assume any non-zero value means True
            result = value != 0
            _LOGGER.debug("Boolean parsing for %s: raw=%d → %s", hex_value, value, result)
            return result
        except (ValueError, TypeError):
            return False

    def _parse_mode(self, hex_value: str) -> str:
        """Parse operating mode from hex register value."""
        try:
            value = int(hex_value, 16)
            
            # Based on your data: 0b89 = "0300" (768)
            # This might be a packed value or different encoding
            # Let's check the low byte first
            low_byte = value & 0xFF
            high_byte = (value >> 8) & 0xFF
            
            _LOGGER.debug("Mode parsing for %s: raw=%d, low_byte=%d, high_byte=%d", 
                         hex_value, value, low_byte, high_byte)
            
            # Try mapping the low byte first
            mode_map = {
                0: "off",
                1: "heat",
                2: "auto", 
                3: "eco",
                4: "comfort",
                5: "boost",
            }
            
            # Try low byte interpretation
            mode = mode_map.get(low_byte, mode_map.get(value, "unknown"))
            _LOGGER.debug("Mode result: %s", mode)
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

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
            
            # Try the new EKD API first, fall back to old API if needed
            try:
                _LOGGER.debug("Attempting EKD API call...")
                ekd_data = await self._get_ekd_data()
                if ekd_data:
                    _LOGGER.info("Successfully retrieved EKD API data with %d variables", len(ekd_data))
                    return self._parse_ekd_status(ekd_data)
                else:
                    _LOGGER.warning("EKD API returned empty data, falling back to legacy API")
            except Exception as exc:
                _LOGGER.warning("EKD API failed, falling back to legacy API: %s", exc)
                _LOGGER.debug("EKD API error details:", exc_info=True)
            
            # Fallback to legacy register API
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
                "current_temperature": self._parse_temperature(registers.get("0c1c", "0000"), "0c1c"),
                "target_temperature_co": self._parse_temperature(registers.get("0bb8", "0000"), "0bb8"),  # CO set temp
                "target_temperature_cwu": self._parse_temperature(registers.get("0bb9", "0000"), "0bb9"),  # CWU set temp
                "water_temperature": self._parse_temperature(registers.get("0c1d", "0000"), "0c1d"),
                "outside_temperature": self._parse_temperature(registers.get("0c1e", "0000"), "0c1e"),
                "return_temperature": self._parse_temperature(registers.get("0c1f", "0000"), "0c1f"),
                
                # Status indicators
                "heater_running": self._parse_boolean(registers.get("0b30", "0000")),
                "water_heating": self._parse_boolean(registers.get("0b32", "0000")),
                "pump_running": self._parse_boolean(registers.get("0b31", "0000")),
                
                # Operating parameters
                "mode": self._parse_mode(registers.get("0b89", "0000")),
                "power": self._parse_power(registers.get("0c9f", "0000")),
                "error_code": self._parse_error(registers.get("0b62", "0000")),
                
                # Use the CO temperature as the primary target for Home Assistant compatibility
                "target_temperature": self._parse_temperature(registers.get("0bb8", "0000"), "0bb8"),
                
                "last_update": asyncio.get_event_loop().time(),
                "raw_registers": registers,  # Include raw data for debugging
            }
            
            # Add comprehensive register analysis for debugging
            self._log_register_analysis(registers)
            
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

    async def _get_ekd_data(self) -> dict[str, Any]:
        """Get data using the EKD API (manufacturer's preferred method)."""
        if not self._device_id:
            raise KospelAPIError("Device ID not discovered yet")
        
        # Variables from the manufacturer's frontend ref_start() function
        variables = [
            "TEMP_ROOM",                    # Room temperature (current)
            "ROOM_TEMP_SETTING",            # Room temperature setting (target CO)
            "TEMP_EXT",                     # External temperature (outside)
            "DHW_TEMP_SETTING",             # DHW temperature setting (target CWU)
            "DHW_SUPPLY_TEMP",              # DHW supply temperature (water temp)
            "FLAG_BUFFER_TIMETABLE_LOADING_TASK",
            "OPERATING_MODE",               # Operating mode
            "ROOM_TEMP_SETTING_INDEX",      # Room temperature setting index
            "FLAG_ROOM_REGULATOR_INT_EXT",
            "FLAG_CH_MANUAL_AUTO_SETTING",
            "DHW_TEMP_SETTING_INDEX",       # DHW temperature setting index
            "FLAG_DHW_ACTIVATION_NO_YES",
            "FLAG_DHW_TERMOSTAT_INT_EXT",
            "FLAG_MANUAL_MODE_ROOM_TEMP",
            "FLAG_PARTY_MODE",
            "FLAG_VACATION_MODE",
            "FLAG_SUMMER_MODE",
            "FLAG_WINTER_MODE",
            "FLAG_TURBO_MODE_IN_PROGRESS",
            "FLAG_TURBO_MODE_CONDITION_FULFILLED",
            "FLAG_EEPROM_ERROR",
            "FLAG_TEMP_IN_ERROR",
            "FLAG_TEMP_OUT_ERROR",
            "FLAG_SUPPLY_TEMP_ERROR",
            "FLAG_TEMP_INT_ERROR",
            "FLAG_TEMP_EXT_ERROR",
            "FLAG_TEMP_ROOM_ERROR",
            "FLAG_LOW_BATTERY_ERROR",
            "FLAG_PREASSURE_ERROR",
            "FLAG_CH_PUMP_ERROR",
            "FLAG_CH_VALVE_ERROR",
            "FLAG_DHW_VALVE_ERROR",
            "HU_INCLUDED_POWER",
            "FLAG_CH_HEATING",              # Central heating status
            "FLAG_DHW_HEATING",             # DHW heating status
            "FLAG_CH_PUMP_OFF_ON",          # CH pump status
            "FLAG_IN_RP",
        ]
        
        try:
            url = f"{self._base_url}/api/ekd/read/{self._device_id}"
            _LOGGER.debug("EKD API request to: %s with %d variables", url, len(variables))
            
            async with asyncio.timeout(10):
                response = await self._session.post(
                    url,
                    headers={
                        "Accept": "application/vnd.kospel.cmi-v1+json",
                        "Content-Type": "application/json"
                    },
                    json=variables
                )
                
                _LOGGER.debug("EKD API response status: %d", response.status)
                
                if response.status >= 400:
                    response_text = await response.text()
                    _LOGGER.error("EKD API HTTP error %d: %s", response.status, response_text)
                    raise KospelAPIError(f"EKD API HTTP error {response.status}: {response_text}")
                
                data = await response.json()
                _LOGGER.debug("EKD API response data keys: %s", list(data.keys()))
                
                regs = data.get("regs", {})
                
                # Apply signed integer conversion like the frontend does
                for reg_name, value in regs.items():
                    if isinstance(value, int) and (value & 32768) > 0:
                        regs[reg_name] = value - 65536
                
                _LOGGER.debug("Retrieved EKD data: %s", regs)
                return regs
                
        except asyncio.TimeoutError as exc:
            raise KospelAPIError("EKD API timeout") from exc
        except (aiohttp.ClientError, json.JSONDecodeError) as exc:
            raise KospelAPIError(f"EKD API request failed: {exc}") from exc

    def _parse_ekd_status(self, ekd_data: dict[str, Any]) -> dict[str, Any]:
        """Parse status data from EKD API response."""
        try:
            # Parse temperature values - EKD API returns values in 0.1°C resolution
            def parse_ekd_temp(value):
                if value is None or value == 0xFFFF or value == -1:
                    return None
                return float(value) / 10.0
            
            # Parse boolean flags
            def parse_ekd_flag(value):
                if value is None:
                    return False
                return bool(value)
            
            status_data = {
                # Temperature readings (direct from EKD API names)
                "current_temperature": parse_ekd_temp(ekd_data.get("TEMP_ROOM")),
                "target_temperature_co": parse_ekd_temp(ekd_data.get("ROOM_TEMP_SETTING")),
                "target_temperature_cwu": parse_ekd_temp(ekd_data.get("DHW_TEMP_SETTING")),
                "water_temperature": parse_ekd_temp(ekd_data.get("DHW_SUPPLY_TEMP")),
                "outside_temperature": parse_ekd_temp(ekd_data.get("TEMP_EXT")),
                "return_temperature": None,  # Not available in EKD API
                
                # Status indicators (using EKD flags)
                "heater_running": parse_ekd_flag(ekd_data.get("FLAG_CH_HEATING")),
                "water_heating": parse_ekd_flag(ekd_data.get("FLAG_DHW_HEATING")),
                "pump_running": parse_ekd_flag(ekd_data.get("FLAG_CH_PUMP_OFF_ON")),
                
                # Operating parameters
                "mode": self._parse_ekd_mode(ekd_data.get("OPERATING_MODE")),
                "power": ekd_data.get("HU_INCLUDED_POWER"),
                "error_code": 0,  # Parse from error flags if needed
                
                # Use CO temperature as primary target for Home Assistant
                "target_temperature": parse_ekd_temp(ekd_data.get("ROOM_TEMP_SETTING")),
                
                "last_update": asyncio.get_event_loop().time(),
                "raw_ekd_data": ekd_data,  # Include raw EKD data for debugging
            }
            
            _LOGGER.info("Parsed EKD status data: %s", {k: v for k, v in status_data.items() if k != "raw_ekd_data"})
            return status_data
            
        except Exception as exc:
            _LOGGER.error("Failed to parse EKD status: %s", exc)
            raise KospelAPIError("Failed to parse EKD status") from exc

    def _parse_ekd_mode(self, mode_value: int | None) -> str:
        """Parse operating mode from EKD API value."""
        if mode_value is None:
            return "unknown"
        
        # Mode mappings based on typical heating system modes
        mode_map = {
            0: "auto",
            1: "manual",
            2: "off",
            3: "heating",
            4: "summer",
            5: "winter",
        }
        
        return mode_map.get(mode_value, f"mode_{mode_value}")

    def _parse_temperature(self, hex_value: str, register_addr: str = "") -> float | None:
        """Parse temperature from hex register value.
        
        Different register ranges may use different encoding methods.
        """
        try:
            # Convert hex to integer
            value = int(hex_value, 16)
            if value == 0xFFFF:  # Invalid/not available
                return None
            
            # Determine parsing method based on register address range
            if register_addr:
                addr_int = int(register_addr, 16)
                
                # 0x0c1c-0x0c1f range: Current/measured temperatures (use LE/10)
                if 0x0c1c <= addr_int <= 0x0c1f:
                    little_endian = ((value & 0xFF) << 8) | ((value >> 8) & 0xFF)
                    temperature = little_endian / 10.0
                    _LOGGER.debug("Temperature parsing (measured) for %s@%s: LE %d → %.1f°C", 
                                 hex_value, register_addr, little_endian, temperature)
                    return temperature
                
                # 0x0bb8-0x0bb9 range: Target/setpoint temperatures
                # These might be encoded differently or be indices
                elif 0x0bb8 <= addr_int <= 0x0bb9:
                    # Try multiple methods for target temperatures
                    methods = []
                    
                    # Method 1: Little-endian / 10
                    le_value = ((value & 0xFF) << 8) | ((value >> 8) & 0xFF)
                    methods.append(("LE/10", le_value / 10.0))
                    
                    # Method 2: Big-endian / 10  
                    methods.append(("BE/10", value / 10.0))
                    
                    # Method 3: High byte as main temperature
                    high_byte = (value >> 8) & 0xFF
                    low_byte = value & 0xFF
                    if high_byte > 0 and high_byte < 100:  # Reasonable temperature range
                        methods.append(("HB", float(high_byte)))
                    
                    # Method 4: Low byte as main temperature  
                    if low_byte > 0 and low_byte < 100:  # Reasonable temperature range
                        methods.append(("LB", float(low_byte)))
                    
                    # Method 5: Check if it's an index (values like 7°C might be stored as index)
                    # Common heating setpoints: 5, 6, 7, 8, 9, 10, etc.
                    if value in range(50, 150):  # 5.0-15.0°C range encoded as 50-150
                        methods.append(("INDEX/10", value / 10.0))
                    
                    # For now, log all methods and use the most reasonable one
                    _LOGGER.warning("Target temperature parsing for %s@%s (value=%d):", 
                                   hex_value, register_addr, value)
                    for method_name, temp in methods:
                        _LOGGER.warning("  %s: %.1f°C", method_name, temp)
                    
                    # Use the first reasonable method (5-30°C range)
                    for method_name, temp in methods:
                        if 5.0 <= temp <= 30.0:
                            _LOGGER.warning("  → Using %s: %.1f°C", method_name, temp)
                            return temp
                    
                    # If no reasonable method found, use LE/10 as fallback
                    temperature = le_value / 10.0
                    _LOGGER.warning("  → Using fallback LE/10: %.1f°C", temperature)
                    return temperature
            
            # Default method for unknown registers: Little-endian / 10
            little_endian = ((value & 0xFF) << 8) | ((value >> 8) & 0xFF)
            temperature = little_endian / 10.0
            
            _LOGGER.debug("Temperature parsing (default) for %s: LE %d → %.1f°C", 
                         hex_value, little_endian, temperature)
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

    def _log_register_analysis(self, registers: dict[str, str]) -> None:
        """Log comprehensive analysis of all temperature-related registers."""
        _LOGGER.warning("=== KOSPEL REGISTER ANALYSIS FOR DEBUGGING ===")
        
        # Key temperature registers to analyze
        temp_registers = [
            ("0bb8", "Target CO (our current mapping)"),
            ("0bb9", "Target CWU (our current mapping)"),
            ("0c1c", "Current temp (our current mapping)"), 
            ("0c1d", "Water temp (our current mapping)"),
            ("0c1e", "Outside temp (our current mapping)"),
            ("0c1f", "Return temp (our current mapping)"),
        ]
        
        # Also check some other ranges that might contain the real values
        other_registers = [
            ("0c00", "0c00 - potential temp register"),
            ("0c01", "0c01 - potential temp register"),
            ("0c02", "0c02 - potential temp register"),
            ("0c10", "0c10 - potential temp register"),
            ("0c11", "0c11 - potential temp register"),
            ("0c12", "0c12 - potential temp register"),
            ("0c20", "0c20 - potential temp register"),
            ("0bb0", "0bb0 - potential setting register"),
            ("0bb1", "0bb1 - potential setting register"),
            ("0bb2", "0bb2 - potential setting register"),
            ("0bb3", "0bb3 - potential setting register"),
            ("0bb4", "0bb4 - potential setting register"),
            ("0bb5", "0bb5 - potential setting register"),
            ("0bb6", "0bb6 - potential setting register"),
            ("0bb7", "0bb7 - potential setting register"),
            ("0bba", "0bba - potential setting register"),
            ("0bbb", "0bbb - potential setting register"),
        ]
        
        all_registers = temp_registers + other_registers
        
        for reg_addr, description in all_registers:
            hex_value = registers.get(reg_addr, "0000")
            if hex_value == "0000":
                continue
                
            value = int(hex_value, 16)
            if value == 0:
                continue
                
            _LOGGER.warning(f"Register {reg_addr} ({description}): {hex_value} ({value})")
            
            # Try multiple temperature parsing methods
            if "temp" in description.lower():
                le_value = ((value & 0xFF) << 8) | ((value >> 8) & 0xFF)
                methods = [
                    ("LE/10", le_value / 10.0),
                    ("BE/10", value / 10.0),
                    ("LE/100", le_value / 100.0),
                    ("BE/100", value / 100.0),
                    ("High byte", float((value >> 8) & 0xFF)),
                    ("Low byte", float(value & 0xFF)),
                ]
                
                for method_name, temp in methods:
                    if 0 <= temp <= 100:  # Reasonable temperature range
                        _LOGGER.warning(f"  {method_name:10}: {temp:6.1f}°C")
            
            # For setting registers, also check if it could be an index
            if "setting" in description.lower():
                high_byte = (value >> 8) & 0xFF
                low_byte = value & 0xFF
                _LOGGER.warning(f"  Bytes: high={high_byte}, low={low_byte}")
                
                # Check if it could be a temperature lookup
                if 50 <= value <= 300:  # 5.0-30.0°C encoded as 50-300
                    _LOGGER.warning(f"  Index/10: {value/10.0:.1f}°C")
        
        _LOGGER.warning("=== END REGISTER ANALYSIS ===")

    async def close(self) -> None:
        """Close the HTTP session."""
        # Session is managed by Home Assistant, don't close it
        pass

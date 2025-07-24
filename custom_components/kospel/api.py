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
        self._ekd_device_id = None

    async def test_connection(self) -> bool:
        """Test connection to the device and discover device IDs."""
        try:
            # Discover device ID for legacy API (used for initial discovery)
            await self._discover_device_id()
            
            # Discover EKD device ID for EKD API (different ID format)
            await self._discover_ekd_device_id()
            
            # Test if EKD API endpoint exists
            if not await self._test_ekd_endpoint():
                raise KospelAPIError("Device does not support EKD API - please check device firmware version")
            
            # Test EKD API access with full variable set
            ekd_data = await self._get_ekd_data()
            if not ekd_data:
                raise KospelAPIError("EKD API test failed - no data returned")
            
            _LOGGER.info("Connection test successful - EKD API working with %d variables", len(ekd_data))
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
            # Ensure both device IDs are discovered before attempting EKD API calls
            if not self._device_id:
                _LOGGER.debug("Device ID not yet discovered, attempting discovery...")
                await self._discover_device_id()
                
            if not self._ekd_device_id:
                _LOGGER.debug("EKD device ID not yet discovered, attempting discovery...")
                await self._discover_ekd_device_id()
            
            # Use EKD API exclusively - this is the manufacturer's preferred method
            _LOGGER.info("Retrieving data via EKD API...")
            try:
                ekd_data = await self._get_ekd_data()
                
                if not ekd_data:
                    raise KospelAPIError("EKD API returned empty data - device may not support EKD API")
                
                _LOGGER.info("✅ EKD API successful with %d variables", len(ekd_data))
                return self._parse_ekd_status(ekd_data)
                
            except KospelAPIError:
                raise
            except Exception as exc:
                _LOGGER.error("EKD API call failed with exception: %s", exc)
                raise KospelAPIError(f"EKD API failed: {exc}") from exc
            
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

    async def _discover_ekd_device_id(self) -> None:
        """Discover EKD device ID using the sessionDevice endpoint."""
        try:
            async with asyncio.timeout(10):
                response = await self._session.get(
                    f"{self._base_url}/api/sessionDevice",
                    headers={
                        "Accept": "application/vnd.kospel.cmi-v1+json"
                    }
                )
                
                if response.status >= 400:
                    raise KospelConnectionError(f"sessionDevice API HTTP error {response.status}")
                
                data = await response.json()
                
                if "sessionDevice" not in data:
                    raise KospelConnectionError("sessionDevice API returned no device ID")
                
                self._ekd_device_id = data["sessionDevice"]
                _LOGGER.info("Discovered EKD device ID: %s", self._ekd_device_id)
                
        except asyncio.TimeoutError as exc:
            _LOGGER.error("EKD device discovery timeout")
            raise KospelConnectionError("EKD device discovery timeout") from exc
        except (aiohttp.ClientError, json.JSONDecodeError) as exc:
            _LOGGER.error("EKD device discovery failed: %s", exc)
            raise KospelConnectionError("Unable to discover EKD device ID") from exc



    async def _test_ekd_endpoint(self) -> bool:
        """Test if the EKD API endpoint exists on this device."""
        if not self._ekd_device_id:
            return False
        
        try:
            # Try a simple test with minimal variables
            test_url = f"{self._base_url}/api/ekd/read/{self._ekd_device_id}"
            test_variables = ["TEMP_ROOM"]  # Just test with one common variable
            
            async with asyncio.timeout(5):
                response = await self._session.post(
                    test_url,
                    headers={"Accept": "application/vnd.kospel.cmi-v1+json", "Content-Type": "application/json"},
                    json=test_variables
                )
                
                # If we get anything other than 404, the endpoint exists
                if response.status == 404:
                    _LOGGER.warning("EKD API endpoint not found (404) - device may not support EKD API")
                    return False
                
                return True
                
        except Exception as exc:
            _LOGGER.debug("EKD endpoint test failed: %s", exc)
            return False

    async def _get_ekd_data(self) -> dict[str, Any]:
        """Get data using the EKD API (manufacturer's preferred method)."""
        if not self._ekd_device_id:
            raise KospelAPIError("EKD device ID not discovered yet")
        
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
            url = f"{self._base_url}/api/ekd/read/{self._ekd_device_id}"
            headers = {
                "Accept": "application/vnd.kospel.cmi-v1+json",
                "Content-Type": "application/json"
            }
            _LOGGER.info("EKD API request: POST %s", url)
            _LOGGER.debug("EKD API headers: %s", headers)
            _LOGGER.debug("EKD API variables (%d): %s", len(variables), variables)
            
            async with asyncio.timeout(10):
                response = await self._session.post(
                    url,
                    headers=headers,
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
                if not regs:
                    _LOGGER.error("EKD API returned no 'regs' data. Full response: %s", data)
                    return {}
                
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









    async def close(self) -> None:
        """Close the HTTP session."""
        # Session is managed by Home Assistant, don't close it
        pass

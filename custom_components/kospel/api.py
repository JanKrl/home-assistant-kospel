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
            
            # Try to discover EKD device ID from session first
            await self._discover_ekd_device_id()
            
            # If sessionDevice failed (using fallback), try session initialization
            if self._ekd_device_id == self._device_id:
                _LOGGER.debug("Using fallback device ID - attempting session initialization")
                if await self._try_session_initialization():
                    # Try to get session device ID again after initialization
                    await self._discover_ekd_device_id()
            
            # Test if EKD API endpoint exists
            if not await self._test_ekd_endpoint():
                raise KospelAPIError("Device does not support EKD API - please check device firmware version")
            
            # Test EKD API access with full variable set
            ekd_data = await self._get_ekd_data()
            if not ekd_data:
                raise KospelAPIError("EKD API test failed - no data returned")
            
            _LOGGER.info("Connection test successful - EKD API working with %d variables", len(ekd_data))
            _LOGGER.info("Using device ID: %s, EKD device ID: %s", self._device_id, self._ekd_device_id)
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
            # Use exact timeout from manufacturer's code (5000ms)
            async with asyncio.timeout(5):
                response = await self._session.get(
                    f"{self._base_url}/api/sessionDevice",
                    headers={
                        "Accept": "application/vnd.kospel.cmi-v1+json"
                    }
                )
                
                _LOGGER.debug("sessionDevice response status: %s", response.status)
                
                if response.status == 404:
                    _LOGGER.warning("sessionDevice endpoint not found - device may not support this API version")
                    # Try using the regular device ID as fallback
                    self._ekd_device_id = self._device_id
                    _LOGGER.info("Using fallback device ID for EKD API: %s", self._ekd_device_id)
                    return
                elif response.status == 500:
                    _LOGGER.warning("sessionDevice endpoint returned HTTP 500 - this might be normal if no session is established")
                    # HTTP 500 might be expected if no session exists yet
                    # Try using the regular device ID as fallback
                    self._ekd_device_id = self._device_id
                    _LOGGER.info("Using fallback device ID for EKD API: %s", self._ekd_device_id)
                    return
                elif response.status >= 400:
                    response_text = await response.text()
                    _LOGGER.warning("sessionDevice API HTTP error %s: %s - using fallback device ID", response.status, response_text)
                    self._ekd_device_id = self._device_id
                    _LOGGER.info("Using fallback device ID for EKD API: %s", self._ekd_device_id)
                    return
                
                data = await response.json()
                _LOGGER.debug("sessionDevice response data: %s", data)
                
                if "sessionDevice" not in data:
                    _LOGGER.warning("sessionDevice API returned no device ID - using fallback")
                    self._ekd_device_id = self._device_id
                    _LOGGER.info("Using fallback device ID for EKD API: %s", self._ekd_device_id)
                    return
                
                session_device_id = data["sessionDevice"]
                
                # Check if the session device ID is valid (manufacturer returns -1 for unset)
                if session_device_id == -1 or session_device_id == "-1":
                    _LOGGER.warning("sessionDevice returned -1 (unset) - using fallback device ID")
                    self._ekd_device_id = self._device_id
                    _LOGGER.info("Using fallback device ID for EKD API: %s", self._ekd_device_id)
                    return
                
                self._ekd_device_id = session_device_id
                _LOGGER.info("Successfully discovered EKD device ID from session: %s", self._ekd_device_id)
                
        except asyncio.TimeoutError:
            _LOGGER.warning("EKD device discovery timeout (5s) - using fallback device ID")
            self._ekd_device_id = self._device_id
            _LOGGER.info("Using fallback device ID for EKD API: %s", self._ekd_device_id)
        except (aiohttp.ClientError, json.JSONDecodeError) as exc:
            _LOGGER.warning("EKD device discovery failed (%s) - using fallback device ID", exc)
            self._ekd_device_id = self._device_id
            _LOGGER.info("Using fallback device ID for EKD API: %s", self._ekd_device_id)

    async def _try_session_initialization(self) -> bool:
        """Try to initialize a session by setting the device ID (experimental)."""
        if not self._device_id:
            return False
            
        try:
            _LOGGER.debug("Attempting session initialization with device ID: %s", self._device_id)
            
            async with asyncio.timeout(5):
                response = await self._session.post(
                    f"{self._base_url}/api/sessionDevice",
                    headers={
                        "Accept": "application/vnd.kospel.cmi-v1+json",
                        "Content-Type": "text/plain"
                    },
                    data=str(self._device_id)
                )
                
                _LOGGER.debug("Session initialization response status: %s", response.status)
                
                if response.status < 400:
                    _LOGGER.info("Session initialization successful")
                    return True
                else:
                    response_text = await response.text()
                    _LOGGER.debug("Session initialization failed: %s - %s", response.status, response_text)
                    return False
                    
        except Exception as exc:
            _LOGGER.debug("Session initialization failed: %s", exc)
            return False



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
            "TEMP_ROOM", "ROOM_TEMP_SETTING", "TEMP_WATER", "WATER_TEMP_SETTING", 
            "TEMP_OUTSIDE", "TEMP_RETURN", "FLAG_CH_HEATING", "FLAG_DHW_HEATING", 
            "FLAG_PUMP", "HEATER_MODE", "HEATER_POWER", "ERROR_CODE"
        ]
        
        try:
            url = f"{self._base_url}/api/ekd/read/{self._ekd_device_id}"
            headers = {
                "Accept": "application/vnd.kospel.cmi-v1+json",
                "Content-Type": "application/json"
            }
            # Try the format that matches the manufacturer's frontend
            _LOGGER.debug("EKD API request: URL=%s, device_id=%s, variables=%s", url, self._ekd_device_id, len(variables))
            
            async with asyncio.timeout(10):
                response = await self._session.post(url, headers=headers, json=variables)
                
                if response.status >= 400:
                    response_text = await response.text()
                    _LOGGER.error("EKD API HTTP %s error: %s", response.status, response_text)
                    raise KospelAPIError(f"EKD API HTTP error {response.status}: {response_text}")
                
                response_data = await response.json()
                _LOGGER.debug("EKD API response: %s", response_data)
                
                # Check for API errors in response
                if "status" in response_data and response_data["status"] < 0:
                    error_msg = response_data.get("status_msg", "Unknown error")
                    _LOGGER.error("EKD API returned error: status=%s, message=%s", response_data["status"], error_msg)
                    
                    # If we get WRONG_ID error, maybe try with a different device ID format
                    if "WRONG_ID" in error_msg:
                        _LOGGER.warning("EKD API reports wrong device ID (%s), this device may not support EKD API", self._ekd_device_id)
                    
                    raise KospelAPIError(f"EKD API error: {error_msg}")
                
                if "regs" not in response_data:
                    _LOGGER.error("EKD API response missing 'regs' key: %s", response_data)
                    raise KospelAPIError("EKD API returned invalid response format")
                
                regs_data = response_data["regs"]
                _LOGGER.info("EKD API successful: retrieved %d variables", len(regs_data))
                
                return regs_data
                
        except asyncio.TimeoutError as exc:
            _LOGGER.error("EKD API timeout")
            raise KospelAPIError("EKD API request timeout") from exc
        except (aiohttp.ClientError, json.JSONDecodeError) as exc:
            _LOGGER.error("EKD API communication error: %s", exc)
            raise KospelAPIError("EKD API communication failed") from exc

    def _parse_ekd_status(self, ekd_data: dict[str, Any]) -> dict[str, Any]:
        """Parse status data from EKD API response."""
        # Apply signed integer conversion like the frontend does
        processed_data = {}
        for reg_name, value in ekd_data.items():
            if isinstance(value, int) and (value & 32768) > 0:
                processed_data[reg_name] = value - 65536
            else:
                processed_data[reg_name] = value
        
        _LOGGER.debug("EKD data after signed conversion: %s", processed_data)
        
        # Parse the status based on available variables
        status = {
            # Temperature sensors (divide by 10 for 0.1°C resolution)
            "current_temperature": processed_data.get("TEMP_ROOM", 0) / 10.0 if processed_data.get("TEMP_ROOM") is not None else None,
            "target_temperature_co": processed_data.get("ROOM_TEMP_SETTING", 0) / 10.0 if processed_data.get("ROOM_TEMP_SETTING") is not None else None,
            "water_temperature": processed_data.get("TEMP_WATER", 0) / 10.0 if processed_data.get("TEMP_WATER") is not None else None,
            "target_temperature_cwu": processed_data.get("WATER_TEMP_SETTING", 0) / 10.0 if processed_data.get("WATER_TEMP_SETTING") is not None else None,
            "outside_temperature": processed_data.get("TEMP_OUTSIDE", 0) / 10.0 if processed_data.get("TEMP_OUTSIDE") is not None else None,
            "return_temperature": processed_data.get("TEMP_RETURN", 0) / 10.0 if processed_data.get("TEMP_RETURN") is not None else None,
            
            # Boolean flags
            "heater_running": bool(processed_data.get("FLAG_CH_HEATING", 0)),
            "water_heating": bool(processed_data.get("FLAG_DHW_HEATING", 0)),
            "pump_running": bool(processed_data.get("FLAG_PUMP", 0)),
            
            # Mode and power
            "mode": self._parse_ekd_mode(processed_data.get("HEATER_MODE")),
            "power": processed_data.get("HEATER_POWER", 0),
            "error_code": processed_data.get("ERROR_CODE", 0),
            
            # Raw EKD data for debugging
            "ekd_raw_data": processed_data
        }
        
        _LOGGER.debug("Parsed EKD status: %s", {k: v for k, v in status.items() if k != "ekd_raw_data"})
        return status

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

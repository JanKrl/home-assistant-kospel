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
        device_id: str | None = None,
        device_type: str | None = None,
    ) -> None:
        """Initialize the API client."""
        self._session = session
        self._host = host
        self._port = port
        self._base_url = f"http://{host}:{port}"
        self._device_id = device_id
        self._device_type = device_type
        self._ekd_device_id = None
        self._session_established = False
        self._last_session_time = None

    async def test_connection(self) -> bool:
        """Test connection to the device and discover device IDs."""
        try:
            # If device is not configured, discover it first
            if not self._device_id or not self._device_type:
                await self._discover_device_id()
            
            # Try comprehensive EKD session discovery
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
        max_retries = 2
        
        for attempt in range(max_retries):
            try:
                # Ensure we have a valid session before making API calls
                if not await self._ensure_valid_session():
                    raise KospelAPIError("Failed to establish valid session")

                # Use EKD API exclusively - this is the manufacturer's preferred method
                _LOGGER.debug("Retrieving data via EKD API (attempt %d/%d)...", attempt + 1, max_retries)
                
                ekd_data = await self._get_ekd_data()
                
                if not ekd_data:
                    raise KospelAPIError("EKD API returned empty data - device may not support EKD API")
                
                # Parse the EKD data into status format
                status_data = self._parse_ekd_status(ekd_data)
                
                _LOGGER.debug("Successfully retrieved status data with %d variables", len(ekd_data))
                return status_data
                
            except Exception as exc:
                _LOGGER.error("Failed to get status (attempt %d/%d): %s", attempt + 1, max_retries, exc)
                
                # Check if this is a session-related error and try to recover
                if attempt < max_retries - 1:  # Don't retry on last attempt
                    if await self._handle_session_error(str(exc)):
                        _LOGGER.info("Session re-established, retrying...")
                        continue
                
                # If we've exhausted retries or can't handle the error, re-raise
                if attempt == max_retries - 1:
                    raise KospelAPIError("Failed to get device status after all retries") from exc

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
        """Discover device ID by calling the device API."""
        try:
            async with asyncio.timeout(10):
                response = await self._session.get(f"{self._base_url}/api/dev")
                
                if response.status >= 400:
                    raise KospelConnectionError(f"Device API HTTP error {response.status}")
                
                data = await response.json()
                
                if not data or "devs" not in data:
                    raise KospelConnectionError("Device API returned no device data")
                
                devices = data["devs"]
                _LOGGER.debug("API returned devices data type: %s, content: %s", type(devices), devices)
                
                if not devices:
                    raise KospelConnectionError("No devices found in response")
                
                # Find the first available device (excluding device 254 which is CMI)
                device_id = None
                device_type = None
                
                # Handle both dictionary and list responses from the API
                if isinstance(devices, dict):
                    # Dictionary format: {dev_id: device_info, ...}
                    for dev_id, device_info in devices.items():
                        if int(dev_id) != 254:  # Skip CMI device
                            device_id = device_info.get("moduleID", dev_id)
                            device_type = dev_id
                            _LOGGER.info("Found device: ID=%s, Type=%s, ModuleID=%s", dev_id, device_type, device_id)
                            break
                elif isinstance(devices, list):
                    # List format: [device_info, ...] - assume first device
                    if devices:
                        device_info = devices[0]
                        device_id = device_info.get("moduleID", device_info.get("id"))
                        device_type = device_info.get("type", "unknown")
                        _LOGGER.info("Found device: ID=%s, Type=%s, ModuleID=%s", device_type, device_type, device_id)
                else:
                    raise KospelConnectionError(f"Unexpected devices format: {type(devices)}")
                
                if device_id is None:
                    raise KospelConnectionError("No suitable devices found")
                
                # Store both device ID and type for session establishment
                self._device_id = device_id
                self._device_type = device_type
                
                _LOGGER.info("Discovered device ID: %s (type: %s)", device_id, device_type)
                
        except asyncio.TimeoutError as exc:
            _LOGGER.error("Device discovery timeout")
            raise KospelConnectionError("Device discovery timeout") from exc
        except (aiohttp.ClientError, json.JSONDecodeError) as exc:
            _LOGGER.error("Device discovery failed: %s", exc)
            raise KospelConnectionError("Unable to discover device") from exc

    async def get_available_devices(self) -> list[dict[str, Any]]:
        """Get list of available devices for configuration."""
        try:
            async with asyncio.timeout(10):
                response = await self._session.get(f"{self._base_url}/api/dev")
                
                if response.status >= 400:
                    raise KospelConnectionError(f"Device API HTTP error {response.status}")
                
                data = await response.json()
                
                if not data or "devs" not in data:
                    return []
                
                devices = data["devs"]
                _LOGGER.debug("API returned devices data type: %s, content: %s", type(devices), devices)
                available_devices = []
                
                # Device type names for user-friendly display
                device_type_names = {
                    18: "EKD.M3 Electric Heater",
                    19: "EKCO.M3 Electric Heater", 
                    65: "C.MG3 Gas Heater",
                    81: "C.MW3 Water Heater",
                    254: "C.MI Controller"
                }
                
                # Handle both dictionary and list responses from the API
                if isinstance(devices, dict):
                    # Dictionary format: {dev_id: device_info, ...} (expected format)
                    for dev_id, device_info in devices.items():
                        device_type = int(dev_id)
                        
                        # Skip CMI controller (254) as it's not a heater
                        if device_type == 254:
                            continue
                        
                        device_id = device_info.get("moduleID", dev_id)
                        type_name = device_type_names.get(device_type, f"Unknown Device (Type {device_type})")
                        
                        # Create device name with module number if available
                        if device_type != 254:
                            module_number = int(device_id) - 100 if isinstance(device_id, (int, str)) and int(device_id) > 100 else device_id
                            device_name = f"{type_name} ({module_number})"
                        else:
                            device_name = type_name
                        
                        available_devices.append({
                            "key": f"{device_type}_{device_id}",
                            "device_id": str(device_id),
                            "device_type": str(device_type),
                            "name": device_name,
                            "type_name": type_name,
                            "module_number": module_number if device_type != 254 else None
                        })
                elif isinstance(devices, list):
                    # List format: [device_info, ...] (fallback for some devices)
                    for device_info in devices:
                        device_type = device_info.get("type", device_info.get("id"))
                        
                        # Skip CMI controller (254) as it's not a heater
                        if device_type == 254:
                            continue
                        
                        device_id = device_info.get("moduleID", device_info.get("id"))
                        type_name = device_type_names.get(device_type, f"Unknown Device (Type {device_type})")
                        
                        # Create device name with module number if available
                        if device_type != 254:
                            module_number = int(device_id) - 100 if isinstance(device_id, (int, str)) and int(device_id) > 100 else device_id
                            device_name = f"{type_name} ({module_number})"
                        else:
                            device_name = type_name
                        
                        available_devices.append({
                            "key": f"{device_type}_{device_id}",
                            "device_id": str(device_id),
                            "device_type": str(device_type),
                            "name": device_name,
                            "type_name": type_name,
                            "module_number": module_number if device_type != 254 else None
                        })
                else:
                    _LOGGER.warning(f"Unexpected devices format: {type(devices)}")
                    return []
                
                _LOGGER.info("Found %d available devices", len(available_devices))
                return available_devices
                
        except asyncio.TimeoutError as exc:
            _LOGGER.error("Device discovery timeout")
            raise KospelConnectionError("Device discovery timeout") from exc
        except (aiohttp.ClientError, json.JSONDecodeError) as exc:
            _LOGGER.error("Device discovery failed: %s", exc)
            raise KospelConnectionError("Unable to discover devices") from exc

    async def _discover_ekd_device_id(self) -> None:
        """Discover EKD device ID using the sessionDevice endpoint."""
        # Use the new session establishment method
        if await self._establish_full_session():
            _LOGGER.debug("EKD device ID discovery completed via session management")
        else:
            raise KospelConnectionError("Failed to establish session for EKD device ID discovery")

    async def _get_existing_session(self) -> str | None:
        """Get existing session device ID (equivalent to getSessionDevice())."""
        try:
            # Use exact timeout from manufacturer's code (5000ms)
            async with asyncio.timeout(5):
                response = await self._session.get(
                    f"{self._base_url}/api/sessionDevice",
                    headers={
                        "Accept": "application/vnd.kospel.cmi-v1+json"
                    }
                )
                
                _LOGGER.debug("getSessionDevice response status: %s", response.status)
                
                if response.status >= 400:
                    response_text = await response.text()
                    _LOGGER.debug("getSessionDevice HTTP error %s: %s", response.status, response_text)
                    return None
                
                data = await response.json()
                _LOGGER.debug("getSessionDevice response data: %s", data)
                
                if "sessionDevice" not in data:
                    _LOGGER.debug("getSessionDevice: no sessionDevice in response")
                    return None
                
                session_device_id = data["sessionDevice"]
                _LOGGER.debug("getSessionDevice returned: %s", session_device_id)
                return session_device_id
                
        except Exception as exc:
            _LOGGER.debug("getSessionDevice failed: %s", exc)
            return None

    async def _establish_session(self) -> bool:
        """Try to establish a session by various methods."""
        if not self._device_id or not self._device_type:
            return False
            
        # Method 1: Call selectModule (this is what the UI does!)
        if await self._select_module():
            _LOGGER.debug("Successfully established session via selectModule")
            return True
            
        # Method 2: Try setting session with regular device ID
        if await self._set_session_device(self._device_id):
            _LOGGER.debug("Successfully set session with regular device ID")
            return True
            
        # Method 3: Try with device ID as string
        if await self._set_session_device(str(self._device_id)):
            _LOGGER.debug("Successfully set session with device ID as string")
            return True
            
        # Method 4: Try visiting the web interface first (might auto-establish session)
        if await self._initialize_web_session():
            _LOGGER.debug("Successfully initialized web session")
            return True
            
        _LOGGER.debug("All session establishment methods failed")
        return False

    async def _select_module(self) -> bool:
        """Select module/device to establish session (equivalent to loadModule())."""
        try:
            _LOGGER.debug("Attempting selectModule with ID: %s, devType: %s", self._device_id, self._device_type)
            
            async with asyncio.timeout(10):
                response = await self._session.post(
                    f"{self._base_url}/api/selectModule",
                    data={
                        "id": str(self._device_id),
                        "devType": str(self._device_type)
                    }
                )
                
                _LOGGER.debug("selectModule response status: %s", response.status)
                
                if response.status >= 400:
                    response_text = await response.text()
                    _LOGGER.debug("selectModule HTTP error %s: %s", response.status, response_text)
                    return False
                
                data = await response.json()
                _LOGGER.debug("selectModule response data: %s", data)
                
                # Check if module selection was successful
                if data.get("status") == 0:
                    _LOGGER.info("Module selection successful - session should be established")
                    return True
                else:
                    _LOGGER.warning("Module selection failed: status=%s", data.get("status"))
                    return False
                    
        except Exception as exc:
            _LOGGER.debug("selectModule failed: %s", exc)
            return False

    async def _set_session_device(self, device_id: str | int) -> bool:
        """Set session device ID (equivalent to part of unSetSessionDevice())."""
        try:
            _LOGGER.debug("Attempting to set session device ID: %s", device_id)
            
            async with asyncio.timeout(5):
                response = await self._session.post(
                    f"{self._base_url}/api/sessionDevice",
                    headers={
                        "Accept": "application/vnd.kospel.cmi-v1+json",
                        "Content-Type": "text/plain"
                    },
                    data=str(device_id)
                )
                
                _LOGGER.debug("setSessionDevice response status: %s", response.status)
                
                if response.status < 400:
                    _LOGGER.debug("Session establishment successful")
                    return True
                else:
                    response_text = await response.text()
                    _LOGGER.debug("Session establishment failed: %s - %s", response.status, response_text)
                    return False
                    
        except Exception as exc:
            _LOGGER.debug("Session establishment exception: %s", exc)
            return False

    async def _initialize_web_session(self) -> bool:
        """Try to initialize session by visiting the main web interface."""
        try:
            _LOGGER.debug("Attempting to initialize web session")
            
            async with asyncio.timeout(10):
                # Try to access the main web interface (this might auto-establish a session)
                response = await self._session.get(
                    f"{self._base_url}/",
                    headers={
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        "User-Agent": "Mozilla/5.0 (compatible; Home Assistant Kospel Integration)"
                    }
                )
                
                _LOGGER.debug("Web interface response status: %s", response.status)
                
                if response.status < 400:
                    _LOGGER.debug("Web interface accessible - session might be established")
                    return True
                else:
                    return False
                    
        except Exception as exc:
            _LOGGER.debug("Web session initialization failed: %s", exc)
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
                    
                    # Raise specific error messages that can be caught by session handler
                    if "WRONG_ID" in error_msg:
                        raise KospelAPIError(f"EKD API device ID error: {error_msg}")
                    else:
                        raise KospelAPIError(f"EKD API error: {error_msg}")
                
                if "regs" not in response_data:
                    _LOGGER.error("EKD API response missing 'regs' key: %s", response_data)
                    raise KospelAPIError("EKD API returned invalid response format")
                
                regs_data = response_data["regs"]
                _LOGGER.debug("EKD API successful: retrieved %d variables", len(regs_data))
                
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

    async def _ensure_valid_session(self) -> bool:
        """Ensure we have a valid session, re-establish if needed."""
        import time
        
        current_time = time.time()
        
        # Check if session might be expired (30 minutes is a common timeout)
        session_age = None
        if self._last_session_time:
            session_age = current_time - self._last_session_time
            
        # Re-establish session if:
        # 1. Never established
        # 2. Older than 25 minutes (proactive refresh)
        # 3. Previous session check failed
        if (not self._session_established or 
            (session_age and session_age > 1500) or  # 25 minutes
            not await self._check_session_validity()):
            
            _LOGGER.debug("Session invalid or expired, re-establishing...")
            return await self._establish_full_session()
        
        return True

    async def _check_session_validity(self) -> bool:
        """Check if current session is still valid."""
        try:
            # Try to get session device ID - if this fails, session is invalid
            session_id = await self._get_existing_session()
            
            # Valid session should return a real device ID (not -1 or None)
            if session_id and session_id != -1 and session_id != "-1":
                _LOGGER.debug("Session validation successful: %s", session_id)
                return True
            else:
                _LOGGER.debug("Session validation failed: invalid session ID")
                return False
                
        except Exception as exc:
            _LOGGER.debug("Session validation failed: %s", exc)
            return False

    async def _establish_full_session(self) -> bool:
        """Establish complete session from scratch."""
        import time
        
        try:
            # Reset session state
            self._session_established = False
            self._ekd_device_id = None
            
            # Ensure we have device info
            if not self._device_id or not self._device_type:
                await self._discover_device_id()
            
            # Establish session
            if await self._establish_session():
                # Get the session device ID
                session_id = await self._get_existing_session()
                if session_id and session_id != -1 and session_id != "-1":
                    self._ekd_device_id = session_id
                    self._session_established = True
                    self._last_session_time = time.time()
                    _LOGGER.info("Session fully established: device_id=%s, session_id=%s", 
                               self._device_id, self._ekd_device_id)
                    return True
            
            # Fallback: use regular device ID
            _LOGGER.warning("Failed to establish session, using fallback device ID")
            self._ekd_device_id = self._device_id
            self._session_established = True  # Mark as established to avoid infinite loops
            self._last_session_time = time.time()
            return True
            
        except Exception as exc:
            _LOGGER.error("Failed to establish session: %s", exc)
            return False

    async def _handle_session_error(self, error_msg: str) -> bool:
        """Handle session-related errors by re-establishing session."""
        session_errors = [
            "WRONG_ID", "SESSION", "UNAUTHORIZED", "FORBIDDEN",
            "500", "502", "503", "504"  # Common session timeout errors
        ]
        
        # Check if error indicates session problem
        if any(err in str(error_msg).upper() for err in session_errors):
            _LOGGER.warning("Detected session error (%s), attempting re-establishment", error_msg)
            
            # Mark session as invalid
            self._session_established = False
            
            # Try to re-establish
            return await self._establish_full_session()
        
        return False

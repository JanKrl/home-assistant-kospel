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


class KospelAPI:
    """API client for Kospel electric heaters using REST API."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        port: int = 80,
        device_id: str | None = None,
        device_type: str | None = None,
        debug_logging: bool = False,
    ) -> None:
        """Initialize the API client."""
        self._session = session
        self._host = host
        self._port = port
        self._base_url = f"http://{host}:{port}"
        self._device_id = device_id
        self._device_type = device_type
        self._debug_logging = debug_logging
        self._ekd_device_id = None
        
        # Set logger level based on debug configuration
        if self._debug_logging:
            _LOGGER.setLevel(logging.DEBUG)
            _LOGGER.debug("KospelAPI initialized with debug logging enabled")
            _LOGGER.debug("API base URL: %s", self._base_url)
            _LOGGER.debug("Initial device_id: %s, device_type: %s", device_id, device_type)
        else:
            _LOGGER.setLevel(logging.INFO)

    async def test_connection(self) -> bool:
        """Test connection to the device and discover device IDs."""
        _LOGGER.debug("Starting connection test to Kospel device")
        _LOGGER.debug("Current device_id: %s, device_type: %s", self._device_id, self._device_type)
        
        try:
            # Ensure device is discovered
            await self._ensure_connection()
            
            # Test EKD API access
            _LOGGER.debug("Testing EKD API data retrieval")
            ekd_data = await self._get_ekd_data()
            if not ekd_data:
                raise KospelAPIError("EKD API test failed - no data returned")
            
            _LOGGER.info("Connection test successful - EKD API working with %d variables", len(ekd_data))
            _LOGGER.info("Using device ID: %s, EKD device ID: %s", self._device_id, self._ekd_device_id)
            
            _LOGGER.debug("Connection test completed successfully")
            _LOGGER.debug("Final device_id: %s, device_type: %s, ekd_device_id: %s", 
                         self._device_id, self._device_type, self._ekd_device_id)
            
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
            # Ensure we have a valid connection
            await self._ensure_connection()

            # Use EKD API - this is the manufacturer's preferred method
            _LOGGER.debug("Retrieving data via EKD API...")
            
            ekd_data = await self._get_ekd_data()
            
            if not ekd_data:
                raise KospelAPIError("EKD API returned empty data - device may not support EKD API")
            
            # Parse the EKD data into status format
            status_data = self._parse_ekd_status(ekd_data)
            
            _LOGGER.debug("Successfully retrieved status data with %d variables", len(ekd_data))
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

    async def _ensure_connection(self) -> bool:
        """Ensure device is discovered and connection is ready."""
        if not self._device_id or not self._device_type:
            _LOGGER.debug("Device not configured, starting device discovery")
            await self._discover_device_id()
        
        if not self._ekd_device_id:
            _LOGGER.debug("EKD device ID not set, using regular device ID")
            self._ekd_device_id = self._device_id
        
        return True

    async def _discover_device_id(self) -> None:
        """Discover device ID by calling the device API."""
        _LOGGER.debug("Starting device ID discovery")
        _LOGGER.debug("Calling API endpoint: %s/api/dev", self._base_url)
        
        try:
            async with asyncio.timeout(10):
                response = await self._session.get(f"{self._base_url}/api/dev")
                
                _LOGGER.debug("Device API response status: %s", response.status)
                
                if response.status >= 400:
                    raise KospelConnectionError(f"Device API HTTP error {response.status}")
                
                data = await response.json()
                
                _LOGGER.debug("Device API response data: %s", data)
                
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
                
                # Store both device ID and type
                self._device_id = device_id
                self._device_type = device_type
                
                _LOGGER.info("Discovered device ID: %s (type: %s)", device_id, device_type)
                
        except asyncio.TimeoutError as exc:
            _LOGGER.error("Device discovery timeout")
            raise KospelConnectionError("Device discovery timeout") from exc
        except (aiohttp.ClientError, json.JSONDecodeError) as exc:
            _LOGGER.error("Device discovery failed: %s", exc)
            raise KospelConnectionError("Unable to discover device") from exc

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
            "target_temperature": processed_data.get("ROOM_TEMP_SETTING", 0) / 10.0 if processed_data.get("ROOM_TEMP_SETTING") is not None else None,
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

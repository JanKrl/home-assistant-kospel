"""API client for Kospel Electric Heaters."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import aiohttp
from homeassistant.exceptions import HomeAssistantError

from .const import API_CONTROL, API_SETTINGS, API_STATUS

_LOGGER = logging.getLogger(__name__)


class KospelAPIError(HomeAssistantError):
    """Exception to indicate a general API error."""


class KospelConnectionError(KospelAPIError):
    """Exception to indicate a connection error."""


class KospelAuthError(KospelAPIError):
    """Exception to indicate an authentication error."""


class KospelAPI:
    """API client for Kospel electric heaters."""

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

    async def test_connection(self) -> bool:
        """Test connection to the device."""
        try:
            async with asyncio.timeout(10):
                response = await self._session.get(f"{self._base_url}/")
                return response.status < 400
        except (asyncio.TimeoutError, aiohttp.ClientError) as exc:
            _LOGGER.error("Connection test failed: %s", exc)
            raise KospelConnectionError("Unable to connect to device") from exc

    async def get_status(self) -> dict[str, Any]:
        """Get current status from the heater."""
        try:
            data = await self._make_request("GET", API_STATUS)
            return data
        except Exception as exc:
            _LOGGER.error("Failed to get status: %s", exc)
            raise KospelAPIError("Failed to get device status") from exc

    async def get_settings(self) -> dict[str, Any]:
        """Get current settings from the heater."""
        try:
            data = await self._make_request("GET", API_SETTINGS)
            return data
        except Exception as exc:
            _LOGGER.error("Failed to get settings: %s", exc)
            raise KospelAPIError("Failed to get device settings") from exc

    async def set_temperature(self, temperature: float) -> bool:
        """Set target temperature."""
        try:
            payload = {"target_temperature": temperature}
            await self._make_request("POST", API_CONTROL, payload)
            return True
        except Exception as exc:
            _LOGGER.error("Failed to set temperature: %s", exc)
            raise KospelAPIError("Failed to set temperature") from exc

    async def set_mode(self, mode: str) -> bool:
        """Set operating mode."""
        try:
            payload = {"mode": mode}
            await self._make_request("POST", API_CONTROL, payload)
            return True
        except Exception as exc:
            _LOGGER.error("Failed to set mode: %s", exc)
            raise KospelAPIError("Failed to set mode") from exc

    async def _make_request(
        self, method: str, endpoint: str, data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Make a request to the API."""
        url = f"{self._base_url}{endpoint}"
        
        headers = {
            "Content-Type": "application/json",
        }
        
        # Add authentication if provided
        auth = None
        if self._username and self._password:
            auth = aiohttp.BasicAuth(self._username, self._password)
        
        try:
            async with asyncio.timeout(10):
                if method.upper() == "GET":
                    async with self._session.get(url, headers=headers, auth=auth) as response:
                        return await self._handle_response(response)
                elif method.upper() == "POST":
                    async with self._session.post(
                        url, headers=headers, auth=auth, json=data
                    ) as response:
                        return await self._handle_response(response)
                else:
                    raise KospelAPIError(f"Unsupported HTTP method: {method}")
                    
        except asyncio.TimeoutError as exc:
            raise KospelConnectionError("Request timeout") from exc
        except aiohttp.ClientError as exc:
            raise KospelConnectionError(f"Connection error: {exc}") from exc

    async def _handle_response(self, response: aiohttp.ClientResponse) -> dict[str, Any]:
        """Handle API response."""
        if response.status == 401:
            raise KospelAuthError("Authentication failed")
        
        if response.status >= 400:
            error_text = await response.text()
            raise KospelAPIError(f"API error {response.status}: {error_text}")
        
        try:
            return await response.json()
        except json.JSONDecodeError:
            # Return empty dict if no JSON response
            return {}

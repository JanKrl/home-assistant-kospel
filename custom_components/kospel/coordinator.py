"""DataUpdateCoordinator for Kospel Electric Heaters."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import KospelAPI, KospelAPIError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class KospelDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching data from the Kospel device."""

    def __init__(
        self,
        hass: HomeAssistant,
        host: str,
        port: int = 80,
        username: str | None = None,
        password: str | None = None,
        device_id: str | None = None,
        device_type: str | None = None,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        
        session = async_get_clientsession(hass)
        
        self.api = KospelAPI(
            session=session,
            host=host,
            port=port,
            username=username,
            password=password,
            device_id=device_id,
            device_type=device_type,
        )
        
        self.host = host
        self.port = port

    async def async_test_connection(self) -> bool:
        """Test connection to the device during setup."""
        try:
            _LOGGER.debug("Testing connection to Kospel device at %s:%s", self.host, self.port)
            return await self.api.test_connection()
        except KospelAPIError as exc:
            _LOGGER.error("Connection test failed: %s", exc)
            raise

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the device."""
        try:
            # Get device status via EKD API
            status_data = await self.api.get_status()
            
            # Update the last successful update time
            status_data["last_update"] = dt_util.utcnow()
            
            _LOGGER.debug("Data update successful, got %d data points", len(status_data))
            return status_data
            
        except Exception as exc:
            _LOGGER.error("Error communicating with Kospel device: %s", exc)
            
            # Check if we need to handle session issues
            if hasattr(self.api, '_handle_session_error'):
                session_recovered = await self.api._handle_session_error(str(exc))
                if session_recovered:
                    _LOGGER.info("Session recovered, will retry on next update cycle")
            
            raise UpdateFailed(f"Error communicating with Kospel device: {exc}") from exc

    async def async_set_temperature(self, temperature: float) -> None:
        """Set target temperature."""
        try:
            await self.api.set_temperature(temperature)
            # Request an immediate update
            await self.async_request_refresh()
        except KospelAPIError as exc:
            _LOGGER.error("Failed to set temperature: %s", exc)
            raise

    async def async_set_mode(self, mode: str) -> None:
        """Set operating mode."""
        try:
            await self.api.set_mode(mode)
            # Request an immediate update
            await self.async_request_refresh()
        except KospelAPIError as exc:
            _LOGGER.error("Failed to set mode: %s", exc)
            raise

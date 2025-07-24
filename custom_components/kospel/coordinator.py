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
        """Fetch data from API endpoint."""
        try:
            # Get status data - this contains all the sensor data we need
            status_data = await self.api.get_status()
            
            # Return the status data directly (flattened structure for sensors)
            # The sensors expect the data structure to be flat, not nested under "status"
            _LOGGER.debug("Successfully updated data from coordinator")
            return status_data
            
        except KospelAPIError as exc:
            _LOGGER.error("Error communicating with Kospel device: %s", exc)
            raise UpdateFailed(f"Error communicating with Kospel device: {exc}") from exc
        except Exception as exc:
            _LOGGER.exception("Unexpected error during data update")
            raise UpdateFailed(f"Unexpected error: {exc}") from exc

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

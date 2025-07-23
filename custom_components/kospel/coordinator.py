"""DataUpdateCoordinator for Kospel Electric Heaters."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import KospelAPI, KospelAPIError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class KospelDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching data from the Kospel device."""

    def __init__(
        self,
        hass: HomeAssistant,
        host: str,
        port: int = 502,
        slave_id: int = 1,
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
        
        self.api = KospelAPI(
            host=host,
            port=port,
            slave_id=slave_id,
            username=username,
            password=password,
        )
        
        self.host = host
        self.port = port

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API endpoint."""
        try:
            # Get both status and settings data
            status_data = await self.api.get_status()
            settings_data = await self.api.get_settings()
            
            # Combine the data
            data = {
                "status": status_data,
                "settings": settings_data,
                "last_update": self.hass.helpers.event.utcnow(),
            }
            
            _LOGGER.debug("Successfully updated data: %s", data)
            return data
            
        except KospelAPIError as exc:
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

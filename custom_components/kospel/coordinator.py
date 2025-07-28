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
        device_id: str | None = None,
        device_type: str | None = None,
        debug_logging: bool = False,
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
            device_id=device_id,
            device_type=device_type,
            debug_logging=debug_logging,
        )
        
        self.host = host
        self.port = port
        self._debug_logging = debug_logging
        
        # Set logger level based on debug configuration
        if self._debug_logging:
            _LOGGER.setLevel(logging.DEBUG)
            _LOGGER.debug("KospelDataUpdateCoordinator initialized")
            _LOGGER.debug("Host: %s, Port: %s", host, port)
            _LOGGER.debug("Device ID: %s, Device Type: %s", device_id, device_type)
            _LOGGER.debug("Update interval: %s seconds", DEFAULT_SCAN_INTERVAL)
        else:
            _LOGGER.setLevel(logging.INFO)

    async def async_test_connection(self) -> bool:
        """Test connection to the device during setup."""
        _LOGGER.debug("Coordinator: Starting connection test")
        _LOGGER.debug("Coordinator: Testing connection to %s:%s", self.host, self.port)
        
        try:
            _LOGGER.debug("Testing connection to Kospel device at %s:%s", self.host, self.port)
            result = await self.api.test_connection()
            
            _LOGGER.debug("Coordinator: Connection test result: %s", result)
            
            return result
        except KospelAPIError as exc:
            _LOGGER.error("Connection test failed: %s", exc)
            _LOGGER.debug("Coordinator: Connection test failed with KospelAPIError")
            raise

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the device."""
        _LOGGER.debug("Coordinator: Starting data update")
        
        try:
            # Get device status via EKD API
            _LOGGER.debug("Coordinator: Requesting status from API")
            status_data = await self.api.get_status()
            
            # Update the last successful update time
            status_data["last_update"] = dt_util.utcnow()
            
            _LOGGER.debug("Coordinator: Data update successful")
            _LOGGER.debug("Coordinator: Retrieved %d data points", len(status_data))
            _LOGGER.debug("Coordinator: Data keys: %s", list(status_data.keys()))
            
            _LOGGER.debug("Data update successful, got %d data points", len(status_data))
            return status_data
            
        except Exception as exc:
            _LOGGER.error("Error communicating with Kospel device: %s", exc)
            
            _LOGGER.debug("Coordinator: Data update failed with exception: %s", exc)
            
            # Check if we need to handle session issues
            if hasattr(self.api, '_handle_session_error'):
                _LOGGER.debug("Coordinator: Attempting session error recovery")
                session_recovered = await self.api._handle_session_error(str(exc))
                if session_recovered:
                    _LOGGER.info("Session recovered, will retry on next update cycle")
                    _LOGGER.debug("Coordinator: Session recovery successful")
                else:
                    _LOGGER.debug("Coordinator: Session recovery failed")
            
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

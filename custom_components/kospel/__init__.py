"""The Kospel Electric Heaters integration."""
from __future__ import annotations

import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN
from .coordinator import KospelDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.CLIMATE, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Kospel from a config entry."""
    _LOGGER.debug("Setting up Kospel integration for entry: %s", entry.entry_id)
    
    hass.data.setdefault(DOMAIN, {})
    
    # Create HTTP session
    session = async_get_clientsession(hass)
    
    # Create data update coordinator
    coordinator = KospelDataUpdateCoordinator(
        hass=hass,
        session=session,
        host=entry.data["host"],
        port=entry.data.get("port", 80),
        username=entry.data.get("username"),
        password=entry.data.get("password"),
    )
    
    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_config_entry_first_refresh()
    
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    # Forward the setup to the sensor and climate platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading Kospel integration for entry: %s", entry.entry_id)
    
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok

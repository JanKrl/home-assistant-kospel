"""The Kospel Electric Heaters integration."""
from __future__ import annotations

import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, CONF_HOST, CONF_PORT, CONF_USERNAME, CONF_PASSWORD
from homeassistant.core import HomeAssistant

from .const import DOMAIN, DEFAULT_PORT
from .coordinator import KospelDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.CLIMATE, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Kospel from a config entry."""
    _LOGGER.debug("Setting up Kospel integration for entry: %s", entry.entry_id)
    
    hass.data.setdefault(DOMAIN, {})
    
    # Create data update coordinator
    coordinator = KospelDataUpdateCoordinator(
        hass=hass,
        host=entry.data[CONF_HOST],
        port=entry.data.get(CONF_PORT, DEFAULT_PORT),
        username=entry.data.get(CONF_USERNAME),
        password=entry.data.get(CONF_PASSWORD),
    )
    
    # Test connection before first refresh to ensure device discovery works
    try:
        _LOGGER.debug("Testing connection to device before setup")
        await coordinator.async_test_connection()
        _LOGGER.info("Successfully connected to Kospel device at %s:%s", 
                    entry.data[CONF_HOST], entry.data.get(CONF_PORT, DEFAULT_PORT))
    except Exception as exc:
        _LOGGER.error("Failed to connect to Kospel device during setup: %s", exc)
        # Don't fail setup completely, let the coordinator handle retries
        pass
    
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

"""Climate platform for Kospel Electric Heaters."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    MANUFACTURER,
    MAX_TEMP,
    MIN_TEMP,
    MODE_AUTO,
    MODE_ECO,
    MODE_HEAT,
    MODE_OFF,
    TEMP_STEP,
)
from .coordinator import KospelDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

# Map Kospel modes to Home Assistant HVAC modes
KOSPEL_TO_HVAC_MODE = {
    MODE_OFF: HVACMode.OFF,
    MODE_HEAT: HVACMode.HEAT,
    MODE_AUTO: HVACMode.AUTO,
    MODE_ECO: HVACMode.AUTO,  # Map ECO to AUTO for now
}

HVAC_TO_KOSPEL_MODE = {v: k for k, v in KOSPEL_TO_HVAC_MODE.items()}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Kospel climate entities from a config entry."""
    coordinator: KospelDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = [KospelClimate(coordinator, config_entry)]
    async_add_entities(entities)


class KospelClimate(CoordinatorEntity[KospelDataUpdateCoordinator], ClimateEntity):
    """Representation of a Kospel heater as a climate entity."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_target_temperature_step = TEMP_STEP
    _attr_min_temp = MIN_TEMP
    _attr_max_temp = MAX_TEMP
    _attr_hvac_modes = list(HVAC_TO_KOSPEL_MODE.keys())
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.TURN_ON | ClimateEntityFeature.TURN_OFF
    )

    def __init__(
        self,
        coordinator: KospelDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the climate entity."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._attr_unique_id = f"{config_entry.entry_id}_climate"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": f"Kospel Heater ({coordinator.host})",
            "manufacturer": MANUFACTURER,
            "model": "Electric Heater",
            "sw_version": "1.0",
        }

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        if not self.coordinator.data:
            return None
        
        return self.coordinator.data.get("current_temperature")

    @property
    def target_temperature(self) -> float | None:
        """Return the temperature we try to reach."""
        if not self.coordinator.data:
            return None
        
        settings = self.coordinator.data.get("settings", {})
        return settings.get("target_temperature")

    @property
    def hvac_mode(self) -> HVACMode | None:
        """Return current operation mode."""
        if not self.coordinator.data:
            return None
        
        kospel_mode = self.coordinator.data.get("mode", MODE_OFF)
        return KOSPEL_TO_HVAC_MODE.get(kospel_mode, HVACMode.OFF)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        
        await self.coordinator.async_set_temperature(temperature)

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        kospel_mode = HVAC_TO_KOSPEL_MODE.get(hvac_mode)
        if kospel_mode is None:
            _LOGGER.error("Unsupported HVAC mode: %s", hvac_mode)
            return
        
        await self.coordinator.async_set_mode(kospel_mode)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

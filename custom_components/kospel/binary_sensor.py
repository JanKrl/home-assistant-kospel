"""Binary sensor platform for Kospel Electric Heaters."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import KospelDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Kospel binary sensor entities from a config entry."""
    coordinator: KospelDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = [
        KospelWaterHeatingBinarySensor(coordinator, config_entry),
        KospelHeaterRunningBinarySensor(coordinator, config_entry),
        KospelPumpRunningBinarySensor(coordinator, config_entry),
    ]
    async_add_entities(entities)


class KospelBinarySensorBase(CoordinatorEntity[KospelDataUpdateCoordinator], BinarySensorEntity):
    """Base class for Kospel binary sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: KospelDataUpdateCoordinator,
        config_entry: ConfigEntry,
        sensor_type: str,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._sensor_type = sensor_type
        self._attr_unique_id = f"{config_entry.entry_id}_{sensor_type}"

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information about this entity."""
        return {
            "identifiers": {(DOMAIN, self._config_entry.entry_id)},
            "name": f"Kospel Heater ({self.coordinator.host})",
            "manufacturer": MANUFACTURER,
            "model": "Electric Heater with C.MI",
            "sw_version": "1.0",
            "configuration_url": f"http://{self.coordinator.host}:{self.coordinator.port}",
        }

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()


class KospelWaterHeatingBinarySensor(KospelBinarySensorBase):
    """Binary sensor for water heating status."""

    _attr_name = "Water Heating"
    _attr_device_class = BinarySensorDeviceClass.RUNNING

    def __init__(
        self,
        coordinator: KospelDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the water heating binary sensor."""
        super().__init__(coordinator, config_entry, "water_heating")

    @property
    def is_on(self) -> bool | None:
        """Return true if water heating is on."""
        if not self.coordinator.data:
            return None
        
        return self.coordinator.data.get("water_heating", False)

    @property
    def icon(self) -> str:
        """Return the icon."""
        if self.is_on:
            return "mdi:water-thermometer"
        return "mdi:water-thermometer-outline"


class KospelHeaterRunningBinarySensor(KospelBinarySensorBase):
    """Binary sensor for heater running status."""

    _attr_name = "Heater Running"
    _attr_device_class = BinarySensorDeviceClass.RUNNING

    def __init__(
        self,
        coordinator: KospelDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the heater running binary sensor."""
        super().__init__(coordinator, config_entry, "heater_running")

    @property
    def is_on(self) -> bool | None:
        """Return true if heater is running."""
        if not self.coordinator.data:
            return None
        
        return self.coordinator.data.get("heater_running", False)

    @property
    def icon(self) -> str:
        """Return the icon."""
        if self.is_on:
            return "mdi:heating-coil"
        return "mdi:radiator-off"


class KospelPumpRunningBinarySensor(KospelBinarySensorBase):
    """Binary sensor for pump running status."""

    _attr_name = "Pump Running"
    _attr_device_class = BinarySensorDeviceClass.RUNNING

    def __init__(
        self,
        coordinator: KospelDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the pump running binary sensor."""
        super().__init__(coordinator, config_entry, "pump_running")

    @property
    def is_on(self) -> bool | None:
        """Return true if pump is running."""
        if not self.coordinator.data:
            return None
        
        return self.coordinator.data.get("pump_running", False)

    @property
    def icon(self) -> str:
        """Return the icon."""
        if self.is_on:
            return "mdi:pump"
        return "mdi:pump-off"
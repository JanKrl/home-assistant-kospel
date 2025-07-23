"""Sensor platform for Kospel Electric Heaters."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPower, UnitOfTemperature
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
    """Set up Kospel sensor entities from a config entry."""
    coordinator: KospelDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = [
        KospelTemperatureSensor(coordinator, config_entry),
        KospelTargetTemperatureSensor(coordinator, config_entry),
        KospelPowerSensor(coordinator, config_entry),
        KospelModeSensor(coordinator, config_entry),
        KospelWaterTemperatureSensor(coordinator, config_entry),
        KospelWaterHeatingSensor(coordinator, config_entry),
        KospelHeaterStatusSensor(coordinator, config_entry),
        KospelErrorCodeSensor(coordinator, config_entry),
    ]
    async_add_entities(entities)


class KospelSensorBase(CoordinatorEntity[KospelDataUpdateCoordinator], SensorEntity):
    """Base class for Kospel sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: KospelDataUpdateCoordinator,
        config_entry: ConfigEntry,
        sensor_type: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._sensor_type = sensor_type
        self._attr_unique_id = f"{config_entry.entry_id}_{sensor_type}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": f"Kospel Heater ({coordinator.host})",
            "manufacturer": MANUFACTURER,
            "model": "Electric Heater",
            "sw_version": "1.0",
        }

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()


class KospelTemperatureSensor(KospelSensorBase):
    """Sensor for current temperature."""

    _attr_name = "Current Temperature"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(
        self,
        coordinator: KospelDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the temperature sensor."""
        super().__init__(coordinator, config_entry, "current_temperature")

    @property
    def native_value(self) -> float | None:
        """Return the current temperature."""
        if not self.coordinator.data:
            return None
        
        status = self.coordinator.data.get("status", {})
        return status.get("current_temperature")


class KospelTargetTemperatureSensor(KospelSensorBase):
    """Sensor for target temperature."""

    _attr_name = "Target Temperature"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(
        self,
        coordinator: KospelDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the target temperature sensor."""
        super().__init__(coordinator, config_entry, "target_temperature")

    @property
    def native_value(self) -> float | None:
        """Return the target temperature."""
        if not self.coordinator.data:
            return None
        
        settings = self.coordinator.data.get("settings", {})
        return settings.get("target_temperature")


class KospelPowerSensor(KospelSensorBase):
    """Sensor for power consumption."""

    _attr_name = "Power"
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfPower.WATT

    def __init__(
        self,
        coordinator: KospelDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the power sensor."""
        super().__init__(coordinator, config_entry, "power")

    @property
    def native_value(self) -> float | None:
        """Return the power consumption."""
        if not self.coordinator.data:
            return None
        
        status = self.coordinator.data.get("status", {})
        return status.get("power")


class KospelModeSensor(KospelSensorBase):
    """Sensor for operating mode."""

    _attr_name = "Mode"
    _attr_icon = "mdi:thermostat"

    def __init__(
        self,
        coordinator: KospelDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the mode sensor."""
        super().__init__(coordinator, config_entry, "mode")

    @property
    def native_value(self) -> str | None:
        """Return the operating mode."""
        if not self.coordinator.data:
            return None
        
        status = self.coordinator.data.get("status", {})
        return status.get("mode")


class KospelWaterTemperatureSensor(KospelSensorBase):
    """Sensor for water heating temperature."""

    _attr_name = "Water Temperature"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(
        self,
        coordinator: KospelDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the water temperature sensor."""
        super().__init__(coordinator, config_entry, "water_temperature")

    @property
    def native_value(self) -> float | None:
        """Return the water temperature."""
        if not self.coordinator.data:
            return None
        
        status = self.coordinator.data.get("status", {})
        return status.get("water_temperature")


class KospelWaterHeatingSensor(KospelSensorBase):
    """Sensor for water heating status."""

    _attr_name = "Water Heating"
    _attr_icon = "mdi:water-thermometer"
    _attr_device_class = SensorDeviceClass.RUNNING

    def __init__(
        self,
        coordinator: KospelDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the water heating sensor."""
        super().__init__(coordinator, config_entry, "water_heating")

    @property
    def native_value(self) -> str | None:
        """Return the water heating status."""
        if not self.coordinator.data:
            return None
        
        status = self.coordinator.data.get("status", {})
        return "on" if status.get("water_heating") else "off"

    @property
    def icon(self) -> str:
        """Return the icon."""
        if not self.coordinator.data:
            return "mdi:water-thermometer-outline"
        
        status = self.coordinator.data.get("status", {})
        if status.get("water_heating"):
            return "mdi:water-thermometer"
        return "mdi:water-thermometer-outline"


class KospelHeaterStatusSensor(KospelSensorBase):
    """Sensor for heater running status."""

    _attr_name = "Heater Running"
    _attr_icon = "mdi:heating-coil"
    _attr_device_class = SensorDeviceClass.RUNNING

    def __init__(
        self,
        coordinator: KospelDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the heater status sensor."""
        super().__init__(coordinator, config_entry, "heater_running")

    @property
    def native_value(self) -> str | None:
        """Return the heater running status."""
        if not self.coordinator.data:
            return None
        
        status = self.coordinator.data.get("status", {})
        return "on" if status.get("heater_running") else "off"

    @property
    def icon(self) -> str:
        """Return the icon."""
        if not self.coordinator.data:
            return "mdi:heating-coil"
        
        status = self.coordinator.data.get("status", {})
        if status.get("heater_running"):
            return "mdi:heating-coil"
        return "mdi:radiator-off"


class KospelErrorCodeSensor(KospelSensorBase):
    """Sensor for error codes."""

    _attr_name = "Error Code"
    _attr_icon = "mdi:alert-circle"
    _attr_entity_category = "diagnostic"

    def __init__(
        self,
        coordinator: KospelDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the error code sensor."""
        super().__init__(coordinator, config_entry, "error_code")

    @property
    def native_value(self) -> int | None:
        """Return the error code."""
        if not self.coordinator.data:
            return None
        
        status = self.coordinator.data.get("status", {})
        return status.get("error_code", 0)

    @property
    def icon(self) -> str:
        """Return the icon."""
        if not self.coordinator.data:
            return "mdi:check-circle"
        
        status = self.coordinator.data.get("status", {})
        error_code = status.get("error_code", 0)
        if error_code == 0:
            return "mdi:check-circle"
        return "mdi:alert-circle"

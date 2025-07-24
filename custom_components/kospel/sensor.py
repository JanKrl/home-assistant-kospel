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
from homeassistant.helpers.entity import EntityCategory

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
        KospelTargetTemperatureCOSensor(coordinator, config_entry),
        KospelTargetTemperatureCWUSensor(coordinator, config_entry),
        KospelWaterTemperatureSensor(coordinator, config_entry),
        KospelOutsideTemperatureSensor(coordinator, config_entry),
        KospelReturnTemperatureSensor(coordinator, config_entry),
        KospelPowerSensor(coordinator, config_entry),
        KospelModeSensor(coordinator, config_entry),
        KospelErrorCodeSensor(coordinator, config_entry),

        # EKD API debug sensor
        KospelEKDDataDebugSensor(coordinator, config_entry),
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
        
        # Data is now returned directly from coordinator (flattened structure)
        return self.coordinator.data.get("current_temperature")


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
        
        return self.coordinator.data.get("target_temperature")


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
        
        return self.coordinator.data.get("power")


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
        
        return self.coordinator.data.get("mode")


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
        
        return self.coordinator.data.get("water_temperature")


class KospelErrorCodeSensor(KospelSensorBase):
    """Sensor for error codes."""

    _attr_name = "Error Code"
    _attr_device_class = None
    _attr_state_class = SensorStateClass.MEASUREMENT

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
        
        return self.coordinator.data.get("error_code", 0)

    @property
    def icon(self) -> str:
        """Return the icon."""
        if not self.coordinator.data:
            return "mdi:alert-circle-outline"
        
        error_code = self.coordinator.data.get("error_code", 0)
        if error_code > 0:
            return "mdi:alert-circle"
        return "mdi:check-circle-outline"


class KospelTargetTemperatureCOSensor(KospelSensorBase):
    """Sensor for CO (Central Heating) target temperature."""

    _attr_name = "Target Temperature CO" 
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(
        self,
        coordinator: KospelDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the CO target temperature sensor."""
        super().__init__(coordinator, config_entry, "target_temperature_co")

    @property
    def native_value(self) -> float | None:
        """Return the CO target temperature."""
        if not self.coordinator.data:
            return None
        
        return self.coordinator.data.get("target_temperature_co")


class KospelTargetTemperatureCWUSensor(KospelSensorBase):
    """Sensor for CWU (Water Heating) target temperature."""

    _attr_name = "Target Temperature CWU"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(
        self,
        coordinator: KospelDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the CWU target temperature sensor."""
        super().__init__(coordinator, config_entry, "target_temperature_cwu")

    @property
    def native_value(self) -> float | None:
        """Return the CWU target temperature."""
        if not self.coordinator.data:
            return None
        
        return self.coordinator.data.get("target_temperature_cwu")


class KospelOutsideTemperatureSensor(KospelSensorBase):
    """Sensor for outside temperature."""

    _attr_name = "Outside Temperature"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(
        self,
        coordinator: KospelDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the outside temperature sensor."""
        super().__init__(coordinator, config_entry, "outside_temperature")

    @property
    def native_value(self) -> float | None:
        """Return the outside temperature."""
        if not self.coordinator.data:
            return None
        
        return self.coordinator.data.get("outside_temperature")


class KospelReturnTemperatureSensor(KospelSensorBase):
    """Sensor for return temperature."""

    _attr_name = "Return Temperature"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(
        self,
        coordinator: KospelDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the return temperature sensor."""
        super().__init__(coordinator, config_entry, "return_temperature")

    @property
    def native_value(self) -> float | None:
        """Return the return temperature."""
        if not self.coordinator.data:
            return None
        
        return self.coordinator.data.get("return_temperature")





class KospelEKDDataDebugSensor(KospelSensorBase):
    """Debug sensor for EKD API data."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:api"

    def __init__(
        self,
        coordinator: KospelDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the EKD debug sensor."""
        super().__init__(coordinator, config_entry, "ekd_debug_data")
        self._attr_name = "EKD API Debug Data"

    @property
    def native_value(self) -> str:
        """Return the EKD API data status."""
        if hasattr(self.coordinator, 'data') and self.coordinator.data:
            ekd_data = self.coordinator.data.get("raw_ekd_data")
            if ekd_data:
                return "EKD API Active"
        return "No Data"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return EKD API data as attributes."""
        if not (hasattr(self.coordinator, 'data') and self.coordinator.data):
            return {"status": "No coordinator data"}
        
        ekd_data = self.coordinator.data.get("raw_ekd_data")
        if not ekd_data:
            return {"status": "EKD API data not available"}
        
        # Format EKD data for display
        formatted_data = {}
        for key, value in ekd_data.items():
            if key.startswith("TEMP_") or key.endswith("_TEMP") or key.endswith("_SETTING"):
                if value is not None and isinstance(value, (int, float)):
                    formatted_data[key] = f"{value} ({value/10.0:.1f}°C)"
                else:
                    formatted_data[key] = str(value)
            elif key.startswith("FLAG_"):
                formatted_data[key] = bool(value) if value is not None else None
            else:
                formatted_data[key] = value
        
        return {
            "api_type": "EKD API v1",
            "variable_count": len(ekd_data),
            **formatted_data
        }

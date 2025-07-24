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
        # Raw register debug sensors
        KospelRawRegisterSensor(coordinator, config_entry, "0c1c", "Current Temperature"),
        KospelRawRegisterSensor(coordinator, config_entry, "0bb8", "CO Target Temperature"),
        KospelRawRegisterSensor(coordinator, config_entry, "0bb9", "CWU Target Temperature"),
        KospelRawRegisterSensor(coordinator, config_entry, "0c1d", "Water Temperature"),
        KospelRawRegisterSensor(coordinator, config_entry, "0c1e", "Outside Temperature"),
        KospelRawRegisterSensor(coordinator, config_entry, "0c1f", "Return Temperature"),
        KospelRawRegisterSensor(coordinator, config_entry, "0b30", "Heater Running"),
        KospelRawRegisterSensor(coordinator, config_entry, "0b31", "Pump Running"),
        KospelRawRegisterSensor(coordinator, config_entry, "0b32", "Water Heating"),
        KospelRawRegisterSensor(coordinator, config_entry, "0b89", "Operating Mode"),
        KospelRawRegisterSensor(coordinator, config_entry, "0c9f", "Power"),
        KospelRawRegisterSensor(coordinator, config_entry, "0b62", "Error Code"),
        # Comprehensive debug sensor
        KospelAllRegistersDebugSensor(coordinator, config_entry),
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


class KospelRawRegisterSensor(KospelSensorBase):
    """Sensor for raw register values (debugging)."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: KospelDataUpdateCoordinator,
        config_entry: ConfigEntry,
        register_address: str,
        register_description: str,
    ) -> None:
        """Initialize the raw register sensor."""
        self._register_address = register_address
        self._register_description = register_description
        self._attr_name = f"Raw {register_description} ({register_address})"
        super().__init__(coordinator, config_entry, f"raw_{register_address}")

    @property
    def native_value(self) -> str | None:
        """Return the raw register value."""
        if not self.coordinator.data:
            return None
        
        raw_registers = self.coordinator.data.get("raw_registers", {})
        raw_value = raw_registers.get(self._register_address, "0000")
        
        # Convert to integer and back to show both hex and decimal
        try:
            int_value = int(raw_value, 16)
            return f"{raw_value} (0x{int_value:04X} = {int_value})"
        except ValueError:
            return raw_value

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:code-brackets"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        if not self.coordinator.data:
            return {}
        
        raw_registers = self.coordinator.data.get("raw_registers", {})
        raw_value = raw_registers.get(self._register_address, "0000")
        
        try:
            int_value = int(raw_value, 16)
            high_byte = (int_value >> 8) & 0xFF
            low_byte = int_value & 0xFF
            
            return {
                "register_address": self._register_address,
                "hex_value": raw_value,
                "decimal_value": int_value,
                "high_byte": f"0x{high_byte:02X} ({high_byte})",
                "low_byte": f"0x{low_byte:02X} ({low_byte})",
                "binary": f"0b{int_value:016b}",
                "description": self._register_description,
            }
        except ValueError:
            return {
                "register_address": self._register_address,
                "hex_value": raw_value,
                "error": "Invalid hex value",
                "description": self._register_description,
            }


class KospelAllRegistersDebugSensor(KospelSensorBase):
    """Sensor showing all register values for comprehensive debugging."""

    _attr_name = "All Raw Registers"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: KospelDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the all registers debug sensor."""
        super().__init__(coordinator, config_entry, "all_raw_registers")

    @property
    def native_value(self) -> str | None:
        """Return the count of available registers."""
        if not self.coordinator.data:
            return None
        
        raw_registers = self.coordinator.data.get("raw_registers", {})
        return f"{len(raw_registers)} registers"

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:database"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return all register values as attributes."""
        if not self.coordinator.data:
            return {}
        
        raw_registers = self.coordinator.data.get("raw_registers", {})
        
        attributes = {
            "register_count": len(raw_registers),
            "last_update": self.coordinator.data.get("last_update"),
        }
        
        # Add each register with both hex and decimal values
        for reg_addr, hex_value in sorted(raw_registers.items()):
            try:
                int_value = int(hex_value, 16)
                attributes[f"reg_{reg_addr}"] = f"{hex_value} ({int_value})"
            except ValueError:
                attributes[f"reg_{reg_addr}"] = hex_value
        
        # Add a formatted summary for easy copying
        register_summary = []
        for reg_addr, hex_value in sorted(raw_registers.items()):
            try:
                int_value = int(hex_value, 16)
                register_summary.append(f"{reg_addr}:{hex_value}({int_value})")
            except ValueError:
                register_summary.append(f"{reg_addr}:{hex_value}")
        
        attributes["formatted_summary"] = " | ".join(register_summary)
        
        return attributes


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
            else:
                return "Legacy API"
        return "No Data"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return EKD API data as attributes."""
        if not (hasattr(self.coordinator, 'data') and self.coordinator.data):
            return {"status": "No coordinator data"}
        
        ekd_data = self.coordinator.data.get("raw_ekd_data")
        if not ekd_data:
            return {"status": "Using legacy register API"}
        
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

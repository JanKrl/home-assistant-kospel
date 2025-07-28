"""Config flow for Kospel Electric Heaters integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DEFAULT_PORT, DOMAIN
from .api import KospelAPI

_LOGGER = logging.getLogger(__name__)

# Configuration constants
CONF_DEVICE_ID = "device_id"
CONF_DEVICE_TYPE = "device_type"
CONF_DEVICE_NAME = "device_name"

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    session = async_get_clientsession(hass)
    
    api = KospelAPI(
        session=session,
        host=data[CONF_HOST],
        port=data.get(CONF_PORT, DEFAULT_PORT),
    )
    
    try:
        # Discover available devices
        await api._discover_device_id()
        
        # Get available devices for selection
        devices = await api.get_available_devices()
        
        return {
            "title": f"Kospel Heater ({data[CONF_HOST]})",
            "devices": devices
        }
        
    except Exception as exc:
        _LOGGER.exception("Unable to connect to Kospel device")
        raise CannotConnect from exc
    finally:
        # Always close the connection
        await api.close()


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Kospel Electric Heaters."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._connection_data: dict[str, Any] = {}
        self._available_devices: list[dict[str, Any]] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - connection details."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                
                # Store connection data for next step
                self._connection_data = user_input
                self._available_devices = info["devices"]
                
                # If no devices found, show error
                if not self._available_devices:
                    errors["base"] = "no_devices"
                else:
                    # Move to device selection step
                    return await self.async_step_device()
                    
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_device(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle device selection step."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            # Get selected device info
            selected_device_key = user_input["device"]
            selected_device = next(
                (dev for dev in self._available_devices if dev["key"] == selected_device_key),
                None
            )
            
            if selected_device:
                # Combine connection data with device selection
                config_data = {
                    **self._connection_data,
                    CONF_DEVICE_ID: selected_device["device_id"],
                    CONF_DEVICE_TYPE: selected_device["device_type"],
                    CONF_DEVICE_NAME: selected_device["name"],
                }
                
                title = f"{selected_device['name']} ({self._connection_data[CONF_HOST]})"
                
                return self.async_create_entry(title=title, data=config_data)
            else:
                errors["base"] = "invalid_device"
        
        # Create device selection schema
        device_options = {
            dev["key"]: dev["name"] for dev in self._available_devices
        }
        
        device_schema = vol.Schema({
            vol.Required("device"): vol.In(device_options)
        })

        return self.async_show_form(
            step_id="device", 
            data_schema=device_schema, 
            errors=errors,
            description_placeholders={
                "device_count": str(len(self._available_devices))
            }
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""




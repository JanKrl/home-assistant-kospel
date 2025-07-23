"""Constants for the Kospel Electric Heaters integration."""

DOMAIN = "kospel"

# Configuration keys
CONF_HOST = "host"
CONF_PORT = "port"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"

# Default values
DEFAULT_PORT = 80
DEFAULT_SCAN_INTERVAL = 30

# Device information
MANUFACTURER = "Kospel"
MODEL_UNKNOWN = "Unknown"

# Heater operating modes
MODE_OFF = "off"
MODE_HEAT = "heat"
MODE_AUTO = "auto"
MODE_ECO = "eco"

MODES = [MODE_OFF, MODE_HEAT, MODE_AUTO, MODE_ECO]

# Temperature limits (in Celsius)
MIN_TEMP = 5
MAX_TEMP = 35
TEMP_STEP = 0.5

# API endpoints (to be defined based on actual Kospel API)
API_STATUS = "/api/status"
API_SETTINGS = "/api/settings"
API_CONTROL = "/api/control"

# Entity names
ENTITY_HEATER = "heater"
ENTITY_TEMPERATURE = "temperature"
ENTITY_TARGET_TEMPERATURE = "target_temperature"
ENTITY_POWER = "power"
ENTITY_MODE = "mode"

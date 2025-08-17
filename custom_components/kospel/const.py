"""Constants for the Kospel Electric Heaters integration."""

DOMAIN = "kospel"

# Configuration keys
CONF_HOST = "host"
CONF_PORT = "port"
CONF_DEBUG_LOGGING = "debug_logging"

# Default values  
DEFAULT_PORT = 80  # HTTP default port
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

# Water heating temperature limits
MIN_WATER_TEMP = 20
MAX_WATER_TEMP = 60

# HTTP API specific constants
HTTP_TIMEOUT = 10
API_DEV_ENDPOINT = "/api/dev"
API_EKD_ENDPOINT = "/api/ekd/read"
API_SELECT_MODULE_ENDPOINT = "/api/selectModule"
API_SESSION_DEVICE_ENDPOINT = "/api/sessionDevice"

# Entity names
ENTITY_HEATER = "heater"
ENTITY_TEMPERATURE = "temperature"
ENTITY_TARGET_TEMPERATURE = "target_temperature"
ENTITY_POWER = "power"
ENTITY_MODE = "mode"

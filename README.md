# Kospel Electric Heaters Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub release](https://img.shields.io/github/release/username/ha-kospel-integration.svg)](https://github.com/username/ha-kospel-integration/releases)
[![GitHub license](https://img.shields.io/github/license/username/ha-kospel-integration.svg)](https://github.com/username/ha-kospel-integration/blob/main/LICENSE)

> [!WARNING]
> **🚧 UNDER ACTIVE DEVELOPMENT 🚧**
> 
> This integration is currently in **experimental stage** and under active development. Use at your own risk!
> 
> - ⚠️ **Not tested with real hardware yet**
> - ⚠️ **Register parsing logic may be incorrect**
> - ⚠️ **Breaking changes may occur without notice** 
> - ⚠️ **No warranty or support guarantees**
> 
> **For developers and testers only!** Production use is not recommended at this time.

A Home Assistant integration for Kospel electric heaters that allows you to monitor and control your heating devices via HTTP REST API using the C.MI internet module.

## Features

- 🌡️ Read current temperature and settings
- 🎯 Set target temperature
- 💧 Monitor water heating status and temperature  
- ⚡ Monitor heater running status and power consumption
- 📊 Monitor operating modes and error codes
- 🔄 Real-time updates via HTTP REST API
- 🏠 Full Home Assistant integration with entities

## Installation

> [!WARNING]
> **READ ALL WARNINGS ABOVE BEFORE INSTALLING**
> 
> Only install if you:
> - Are a developer/tester
> - Understand the risks
> - Have Kospel C.MI hardware for testing
> - Can troubleshoot HTTP API issues

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Navigate to "Integrations"
3. Click the three dots in the top right corner and select "Custom repositories"
4. Add `https://github.com/username/ha-kospel-integration` as repository
5. Select "Integration" as category
6. Click "Add"
7. Search for "Kospel" and install
8. Restart Home Assistant

### Manual Installation

1. Download the latest release from the [releases page](https://github.com/username/ha-kospel-integration/releases)
2. Create a directory called `kospel` in your `custom_components` folder
3. Extract all Python files (`*.py`), `manifest.json`, `strings.json`, and `translations/` folder to `custom_components/kospel/`
4. Restart Home Assistant

## Configuration

### Prerequisites

- Kospel electric heater with C.MI (Internet Module) installed
- C.MI module connected to your network via Ethernet
- Modbus TCP enabled on the C.MI module

### Setup

Add the integration through the Home Assistant UI:

1. Go to Settings → Devices & Services
2. Click "Add Integration"
3. Search for "Kospel"
4. Configure the connection:
   - **Host**: IP address of your C.MI module
   - **Port**: Modbus TCP port (default: 502)
   - **Slave ID**: Modbus device ID (default: 1)
   - **Username/Password**: Optional authentication credentials

## Supported Models

This integration is designed to work with Kospel electric heaters equipped with the C.MI internet module:

- Kospel EPO/EPV series with C.MI
- Kospel EKC series with C.MI  
- Any Kospel heater with C.MI module that supports HTTP REST API

## Protocol Details

The integration uses **HTTP REST API** to communicate with Kospel heaters through the C.MI internet module. The following data is monitored and controlled:

### Monitored Values
- Current room temperature
- Target temperature for CO (Central Heating)
- Target temperature for CWU (Water Heating)
- Water temperature
- Outside temperature (if available)
- Return temperature (if available)
- Heater running status
- Water heating status
- Pump running status
- Operating mode (Off, Heat, Auto, Eco, Manual, Program modes)
- Power consumption
- Error codes

### Controllable Settings
- Target temperature (5°C - 35°C)
- Operating mode
- Water heating temperature (20°C - 60°C)

## Development Status

> [!CAUTION]
> **EXPERIMENTAL SOFTWARE - USE WITH CAUTION**

This integration is currently in **experimental development phase**. Implementation status:

### ✅ **Completed (Theoretical)**
- Basic project structure with HACS support
- HTTP REST API communication protocol implementation
- Temperature reading and control logic
- Water heating monitoring and control logic
- Operating mode control implementation
- Status monitoring (heater running, power, errors)

### ⚠️ **CRITICAL LIMITATIONS**
- **NOT TESTED** with real Kospel C.MI hardware
- **UNKNOWN** if register parsing logic is correct
- **NO VALIDATION** of actual device communication
- **POTENTIAL** for device damage if registers are wrong

### 🚧 **In Development**
- Hardware testing and validation
- Register parsing verification
- Error handling improvements
- Advanced features and configuration options
- Multi-zone support
- Energy monitoring and statistics

### 🎯 **Testing Needed**
- Real Kospel C.MI hardware validation
- Register parsing mapping verification
- Temperature control testing
- Water heating control testing
- Error condition handling

## Important Notes

> [!IMPORTANT]
> **DISCLAIMER: USE AT YOUR OWN RISK**

⚠️ **Protocol Implementation**: The register parsing logic used in this integration is based on analysis of actual API responses. However, the interpretation of register values may not be completely accurate and might need adjustment based on your specific device behavior.

⚠️ **Potential Risks**: Incorrect API commands could potentially damage your heating system. The authors are not responsible for any damage caused by using this integration.

🔧 **For Developers**: If you have access to official Kospel C.MI API documentation or have successfully tested this integration, please contribute by opening issues or pull requests with correct register interpretations.

📋 **Before Using**: 
- Backup your heater settings
- Test in a safe environment first
- Monitor system behavior closely
- Have alternative heating methods available

## Troubleshooting

### Common Issues

#### ❌ "Device ID not discovered yet" Error

If you see this error in your logs:
```
ERROR (MainThread) [custom_components.kospel.api] Failed to get status: Device ID not discovered yet
```

**Solution**: This has been fixed in recent versions. The integration now automatically discovers the device ID when needed. If you still encounter this issue:

1. **Check network connectivity**: Ensure Home Assistant can reach your Kospel device
2. **Verify device IP**: Make sure the IP address in your configuration is correct
3. **Check device status**: Ensure your Kospel C.MI module is powered on and responsive
4. **Test manually**: Use the provided test script to verify connectivity:
   ```bash
   python3 test_device_discovery.py
   ```
   (Update the IP address in the script first)

5. **Enable debug logging**: Add this to your `configuration.yaml`:
   ```yaml
   logger:
     logs:
       custom_components.kospel: debug
   ```

#### ❌ "AttributeError: type object 'SensorDeviceClass' has no attribute 'RUNNING'"

This error occurred in older versions and has been fixed by converting the running status sensors to binary sensors.

**Solution**: Update to version 0.1.2 or later. The water heating and heater running sensors are now properly implemented as binary sensors.

#### 🔄 Integration Won't Initialize

1. Remove and re-add the integration
2. Check Home Assistant logs for specific error messages
3. Verify your device is accessible via HTTP at `http://your-device-ip/api/dev`

#### 📊 Wrong Temperature Values

**Version 0.2.0+ includes the correct EKD API implementation:**
- **EKD API Support**: Now uses the manufacturer's preferred `api/ekd/read` endpoint with proper headers
- **Correct Variable Names**: Uses the same variable names as the manufacturer's frontend (`TEMP_ROOM`, `ROOM_TEMP_SETTING`, etc.)
- **Proper Data Processing**: Includes signed integer conversion and 0.1°C resolution handling
- **Fallback Support**: Automatically falls back to legacy register API if EKD API fails

**Major Breakthrough**: Analysis of the manufacturer's JavaScript revealed they use a completely different API endpoint (`api/ekd/read/{device_id}`) with named variables instead of raw register addresses. This should resolve all temperature accuracy issues.

**EKD API Features:**
- Direct temperature readings in 0.1°C resolution
- Proper boolean flag handling
- Signed integer support for negative temperatures
- Same variable names as manufacturer frontend

If you still see incorrect values after updating to v0.2.0+:
1. Check the raw register debug sensors to verify hex values match expectations
2. Compare with manufacturer frontend values  
3. Report any discrepancies with register address, raw hex, expected value, and actual parsed value

## Debugging Features (v0.1.4+)

To help identify and fix register parsing issues, the integration now includes comprehensive debugging sensors:

### Raw Register Sensors
Each important register has a corresponding "Raw" diagnostic sensor that shows:
- **Raw hex value** from the device
- **Decimal equivalent** 
- **High/low byte breakdown**
- **Binary representation**

Look for entities named like:
- `Raw Current Temperature (0c1c)`
- `Raw CO Target Temperature (0bb8)`
- `Raw CWU Target Temperature (0bb9)`
- etc.

### All Registers Debug Sensor
The `All Raw Registers` sensor provides:
- **Complete register dump** as entity attributes
- **Formatted summary** for easy copying/pasting
- **Register count** as the main state

### Debug Helper Script
Use the included `debug_helper.py` script to:
1. **Compare manufacturer values** with register values
2. **Test all parsing methods** automatically  
3. **Identify the correct interpretation** for each register

```bash
python3 debug_helper.py
```

### How to Debug Temperature Issues

**New in v0.2.0**: Check the **EKD API Debug Data** sensor first:
- If it shows "EKD API Active", the integration is using the correct manufacturer API
- If it shows "Legacy API", there may be an issue with EKD API access
- View the sensor attributes to see all EKD variables and their values

**For detailed debugging**:
1. **Note the manufacturer value** from the official frontend  
2. **Check the EKD Debug sensor** for the corresponding variable (e.g., `TEMP_ROOM`, `ROOM_TEMP_SETTING`)
3. **Compare EKD values** with manufacturer values (should match exactly)
4. **If using legacy API**, find the raw register value and use the debug helper script

### Testing Your Setup

You can verify your device connectivity by checking the Home Assistant logs:
1. Enable debug logging for `custom_components.kospel`
2. Restart Home Assistant
3. Check logs for successful device discovery and register retrieval

The raw register debug sensors will show "0000" values if communication fails.

## Contributing

Contributions are welcome! Please read the contributing guidelines and submit pull requests for any improvements.

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Support

If you encounter any issues, please [open an issue](https://github.com/username/ha-kospel-integration/issues) on GitHub.

# Kospel Electric Heaters Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub release](https://img.shields.io/github/release/username/ha-kospel-integration.svg)](https://github.com/username/ha-kospel-integration/releases)
[![GitHub license](https://img.shields.io/github/license/username/ha-kospel-integration.svg)](https://github.com/username/ha-kospel-integration/blob/main/LICENSE)

A Home Assistant integration for Kospel electric heaters that allows you to monitor and control your heating devices via HTTP REST API using the C.MI internet module.

## Features

- 🌡️ Read current temperature and settings
- 🎯 Set target temperature (planned)
- 💧 Monitor water heating status and temperature  
- ⚡ Monitor heater running status and power consumption
- 📊 Monitor operating modes and error codes
- 🔄 Real-time updates via HTTP REST API
- 🏠 Full Home Assistant integration with entities
- 🐛 Debug logging support for troubleshooting

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Navigate to "Integrations"
3. Click the three dots in the top right corner and select "Custom repositories"
4. Add `https://github.com/JanKrl/home-assistant-kospel` as repository
5. Select "Integration" as category
6. Click "Add"
7. Search for "Kospel" and install
8. Restart Home Assistant

### Manual Installation

1. Download the latest release from the [releases page](https://github.com/JanKrl/home-assistant-kospel/releases)
2. Create a directory called `kospel` in your `custom_components` folder
3. Extract all Python files (`*.py`), `manifest.json`, `strings.json`, and `translations/` folder to `custom_components/kospel/`
4. Restart Home Assistant

## Configuration

### Prerequisites

- Kospel electric heater with C.MI (Internet Module) installed
- C.MI module connected to your network via Ethernet
- HTTP REST API enabled on the C.MI module

### Setup

Add the integration through the Home Assistant UI:

1. Go to Settings → Devices & Services
2. Click "Add Integration"
3. Search for "Kospel"
4. Configure the connection:
   - **Host**: IP address of your C.MI module
   - **Port**: HTTP port (default: 80)
   - **Debug Logging**: Enable for troubleshooting (optional)

## Supported Models

This integration is designed to work with Kospel electric heaters equipped with the C.MI internet module:

- Kospel EPO/EPV series with C.MI
- Kospel EKC series with C.MI  
- Any Kospel heater with C.MI module that supports HTTP REST API

## Protocol Details

The integration uses **HTTP REST API** to communicate with Kospel heaters through the C.MI internet module. The following data is monitored:

### Monitored Values
- Current room temperature
- Target temperature for heating
- Water heating temperature
- Outside temperature (if available)
- Return temperature (if available)
- Heater running status
- Water heating status
- Pump running status
- Operating mode (Off, Heat, Auto, Eco, Manual, Program modes)
- Power consumption
- Error codes

### Planned Features
- Target temperature control
- Operating mode control
- Water heating temperature control

## Troubleshooting

### Common Issues

#### ❌ "Unable to connect to Kospel device" Error

If you see this error during configuration:

**Solution**:
1. **Check network connectivity**: Ensure Home Assistant can reach your Kospel device
2. **Verify device IP**: Make sure the IP address in your configuration is correct
3. **Check device status**: Ensure your Kospel C.MI module is powered on and responsive
4. **Enable debug logging**: Check the debug logging option during configuration to get detailed logs
5. **Check firewall**: Ensure port 80 (or your configured port) is accessible

#### ❌ "No devices found" Error

If the integration can't discover your device:

**Solution**:
1. **Verify API endpoint**: Try accessing `http://[device-ip]/api/dev` in a browser
2. **Check device compatibility**: Ensure your device supports the HTTP REST API
3. **Enable debug logging**: This will show detailed API responses for troubleshooting

#### 🔄 Integration Won't Initialize

**Solution**:
1. **Check logs**: Enable debug logging and check Home Assistant logs
2. **Restart Home Assistant**: After installation, a restart is required
3. **Verify configuration**: Double-check host and port settings

### Debug Logging

Enable debug logging during configuration to get detailed information about:
- API requests and responses
- Device discovery process
- Data parsing and conversion
- Connection status

This is very helpful for troubleshooting issues.

## Development Status

This integration is in active development. Current status:

### ✅ **Completed**
- Basic project structure with HACS support
- HTTP REST API communication protocol implementation
- Temperature reading and monitoring
- Water heating monitoring
- Operating mode monitoring
- Status monitoring (heater running, power, errors)
- Device discovery for multiple API response formats
- Debug logging support

### 🚧 **In Development**
- Temperature control implementation
- Mode control implementation
- Advanced features and configuration options

### 🎯 **Planned**
- Multi-zone support
- Energy monitoring and statistics
- Automation templates
- Performance optimizations

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This integration is not officially affiliated with Kospel. Use at your own risk and ensure you have proper backups of your device settings before testing.

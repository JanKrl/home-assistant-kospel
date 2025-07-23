# Kospel Electric Heaters Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub release](https://img.shields.io/github/release/username/ha-kospel-integration.svg)](https://github.com/username/ha-kospel-integration/releases)
[![GitHub license](https://img.shields.io/github/license/username/ha-kospel-integration.svg)](https://github.com/username/ha-kospel-integration/blob/main/LICENSE)

A Home Assistant integration for Kospel electric heaters that allows you to monitor and control your heating devices via Modbus TCP protocol using the C.MI internet module.

## Features

- 🌡️ Read current temperature and settings
- 🎯 Set target temperature
- 💧 Monitor water heating status and temperature  
- ⚡ Monitor heater running status and power consumption
- 📊 Monitor operating modes and error codes
- 🔄 Real-time updates via Modbus TCP
- 🏠 Full Home Assistant integration with entities

## Installation

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
2. Extract the files to your `custom_components/kospel` directory
3. Restart Home Assistant

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
- Any Kospel heater with C.MI module that supports Modbus TCP

## Protocol Details

The integration uses **Modbus TCP** protocol to communicate with Kospel heaters through the C.MI internet module. The following data is monitored and controlled:

### Monitored Values
- Current room temperature
- Target temperature settings
- Heater running status
- Water heating status and temperature
- Operating mode (Off, Heat, Auto, Eco)
- Power consumption
- Error codes

### Controllable Settings
- Target temperature (5°C - 35°C)
- Operating mode
- Water heating temperature (20°C - 60°C)

## Development Status

This integration is currently in active development. Features are being implemented incrementally:

- ✅ Basic project structure with HACS support
- ✅ Modbus TCP communication protocol
- ✅ Temperature reading and control
- ✅ Water heating monitoring and control
- ✅ Operating mode control
- ✅ Status monitoring (heater running, power, errors)
- ⏳ Advanced features and configuration options
- ⏳ Multi-zone support
- ⏳ Energy monitoring and statistics

## Important Notes

⚠️ **Protocol Implementation**: The Modbus register addresses used in this integration are based on common heating system implementations and research. Since official Kospel C.MI Modbus documentation was not publicly available, the actual register addresses may need adjustment based on your specific device.

🔧 **For Developers**: If you have access to official Kospel C.MI Modbus documentation or have successfully tested this integration, please contribute by opening issues or pull requests with correct register mappings.

## Contributing

Contributions are welcome! Please read the contributing guidelines and submit pull requests for any improvements.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

If you encounter any issues, please [open an issue](https://github.com/username/ha-kospel-integration/issues) on GitHub.

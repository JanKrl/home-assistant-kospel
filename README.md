# Kospel Electric Heaters Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub release](https://img.shields.io/github/release/username/ha-kospel-integration.svg)](https://github.com/username/ha-kospel-integration/releases)
[![GitHub license](https://img.shields.io/github/license/username/ha-kospel-integration.svg)](https://github.com/username/ha-kospel-integration/blob/main/LICENSE)

A Home Assistant integration for Kospel electric heaters that allows you to monitor and control your heating devices.

## Features

- 🌡️ Read current temperature and settings
- 🎯 Set target temperature
- 📊 Monitor heater status and operating modes
- 🔄 Real-time updates
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

Add the integration through the Home Assistant UI:

1. Go to Settings → Devices & Services
2. Click "Add Integration"
3. Search for "Kospel"
4. Follow the configuration steps

## Supported Models

This integration is designed to work with Kospel electric heaters. Initially supporting:

- Kospel EPO/EPV series
- Kospel EKC series
- Additional models will be added incrementally

## Development Status

This integration is currently in active development. Features are being implemented incrementally:

- ✅ Basic project structure
- 🚧 Device discovery and connection
- 🚧 Temperature reading
- 🚧 Temperature control
- ⏳ Advanced features and settings

## Contributing

Contributions are welcome! Please read the contributing guidelines and submit pull requests for any improvements.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

If you encounter any issues, please [open an issue](https://github.com/username/ha-kospel-integration/issues) on GitHub.

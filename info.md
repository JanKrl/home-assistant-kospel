# Kospel Electric Heaters Integration

## Overview
This integration allows Home Assistant to communicate with Kospel electric heaters, providing both monitoring capabilities and control functions.

## Features
- **Temperature Monitoring**: Read current temperature from the heater
- **Temperature Control**: Set target temperature remotely
- **Operating Mode Control**: Switch between different heating modes (Off, Heat, Auto, Eco)
- **Power Monitoring**: Monitor current power consumption
- **Real-time Updates**: Automatic polling for status updates

## Supported Entities
- **Climate Entity**: Main heater control with temperature setting and mode selection
- **Temperature Sensors**: Current and target temperature readings
- **Power Sensor**: Current power consumption
- **Mode Sensor**: Current operating mode

## Installation Methods
1. **HACS (Home Assistant Community Store)** - Recommended
2. **Manual Installation** - Copy files to custom_components directory

## Configuration
The integration uses a configuration flow accessible through the Home Assistant UI. Required information:
- Host IP address of the Kospel heater
- Port (default: 80)
- Username/Password (if authentication is required)

## Development Notes
This integration is designed with extensibility in mind:
- Modular API client for easy protocol adaptation
- Coordinator pattern for efficient data management
- Comprehensive error handling and logging
- Type hints throughout for better code quality

## Future Enhancements
- Support for additional Kospel heater models
- Advanced scheduling features
- Energy usage tracking
- Multiple zone support
- Enhanced error recovery

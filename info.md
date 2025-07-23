# Kospel Electric Heaters Integration

## Overview
This integration allows Home Assistant to communicate with Kospel electric heaters equipped with C.MI internet modules via Modbus TCP protocol, providing comprehensive monitoring and control capabilities.

## Features
- **Temperature Monitoring**: Read current room temperature from the heater
- **Temperature Control**: Set target temperature remotely (5°C - 35°C)
- **Water Heating Control**: Monitor and control water heating (20°C - 60°C)
- **Operating Mode Control**: Switch between heating modes (Off, Heat, Auto, Eco)
- **Status Monitoring**: Monitor heater running status, water heating, and error codes
- **Power Monitoring**: Track current power consumption
- **Real-time Updates**: Automatic polling via Modbus TCP

## Supported Entities
- **Climate Entity**: Main heater control with temperature setting and mode selection
- **Temperature Sensors**: Current, target, and water temperature readings
- **Status Sensors**: Heater running, water heating, operating mode
- **Power Sensor**: Current power consumption
- **Diagnostic Sensor**: Error code monitoring

## Protocol
Uses **Modbus TCP** communication through Kospel C.MI internet module:
- **Port**: 502 (Modbus TCP standard)
- **Protocol**: Modbus TCP over Ethernet
- **Device**: Kospel C.MI internet module

## Installation Methods
1. **HACS (Home Assistant Community Store)** - Recommended
2. **Manual Installation** - Copy files to custom_components directory

## Configuration
The integration uses a configuration flow accessible through the Home Assistant UI. Required information:
- **Host**: IP address of the C.MI module  
- **Port**: Modbus TCP port (default: 502)
- **Slave ID**: Modbus device ID (default: 1)
- **Username/Password**: Optional authentication credentials

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

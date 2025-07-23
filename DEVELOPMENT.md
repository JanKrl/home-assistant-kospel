# Kospel C.MI Integration Development Guide

## Overview

This Home Assistant integration communicates with Kospel electric heaters through their C.MI (Internet Module) using the **Modbus TCP** protocol. This document provides technical details for developers and users who want to understand or modify the integration.

## Protocol Details

### Communication Method
- **Protocol**: Modbus TCP
- **Port**: 502 (standard Modbus TCP port)
- **Device**: Kospel C.MI Internet Module
- **Connection**: Ethernet/WiFi to Home Assistant

### Modbus Register Mapping

The following register addresses are implemented based on common heating system patterns. **Note**: These may need adjustment based on actual Kospel C.MI documentation.

#### Status Registers (Read-Only)
| Address | Register | Description | Data Type | Unit |
|---------|----------|-------------|-----------|------|
| 0x0001 | Current Temperature | Room temperature | uint16 | °C × 10 |
| 0x0002 | Target Temperature | Set temperature | uint16 | °C × 10 |
| 0x0003 | Heater Status | Running status | uint16 | 0=off, 1=on |
| 0x0004 | Operating Mode | Current mode | uint16 | 0=off, 1=heat, 2=auto, 3=eco |
| 0x0005 | Water Heating Status | Water heating on/off | uint16 | 0=off, 1=on |
| 0x0006 | Water Temperature | Water target temp | uint16 | °C × 10 |
| 0x0007 | Power Consumption | Current power draw | uint16 | Watts |
| 0x0008 | Error Code | System error status | uint16 | 0=no error |

#### Control Registers (Write)
| Address | Register | Description | Data Type | Unit |
|---------|----------|-------------|-----------|------|
| 0x0102 | Set Target Temperature | Change room temp | uint16 | °C × 10 |
| 0x0103 | Set Operating Mode | Change mode | uint16 | 0-3 |
| 0x0104 | Set Heater On/Off | Enable/disable | uint16 | 0=off, 1=on |
| 0x0105 | Set Water Temperature | Change water temp | uint16 | °C × 10 |

## Implementation Details

### Key Components

1. **api.py** - Modbus TCP communication layer
2. **coordinator.py** - Data polling and state management
3. **climate.py** - Climate entity for temperature control
4. **sensor.py** - Various sensor entities
5. **config_flow.py** - Configuration UI

## Known Limitations

### Register Address Uncertainty
The Modbus register addresses used are **estimated** based on:
- Common heating system implementations
- Similar Buderus/Bosch integrations
- Industrial Modbus conventions

**Important**: Actual Kospel C.MI register addresses may differ and require adjustment.

## Contributing

### Documentation Needed
- Official Kospel C.MI Modbus register documentation
- Testing results with real hardware
- Additional sensor types and capabilities

### Testing
Before submitting changes:
1. Test with actual Kospel C.MI hardware
2. Verify all entity states update correctly
3. Check error handling scenarios
4. Validate temperature control functions

## References

- [Modbus TCP Specification](https://modbus.org/docs/Modbus_Application_Protocol_V1_1b3.pdf)
- [Home Assistant Integration Development](https://developers.home-assistant.io/docs/creating_integration_index/)
- [PyModbus Documentation](https://pymodbus.readthedocs.io/)

# Kospel API Reference

This document covers both the EKD API (preferred) and legacy register API (fallback).

## EKD API (v0.2.0+) - **RECOMMENDED**

The integration now uses the manufacturer's EKD API which provides direct access to named variables.

### Key EKD Variables

| Variable Name | Description | Resolution | Example |
|---------------|-------------|------------|---------|
| `TEMP_ROOM` | Room temperature (current) | 0.1°C | 230 = 23.0°C |
| `ROOM_TEMP_SETTING` | Room temperature setting (target CO) | 0.1°C | 70 = 7.0°C |
| `TEMP_EXT` | External temperature (outside) | 0.1°C | 125 = 12.5°C |
| `DHW_TEMP_SETTING` | DHW temperature setting (target CWU) | 0.1°C | 70 = 7.0°C |
| `DHW_SUPPLY_TEMP` | DHW supply temperature | 0.1°C | 550 = 55.0°C |
| `FLAG_CH_HEATING` | Central heating status | Boolean | 1 = ON, 0 = OFF |
| `FLAG_DHW_HEATING` | DHW heating status | Boolean | 1 = ON, 0 = OFF |
| `FLAG_CH_PUMP_OFF_ON` | CH pump status | Boolean | 1 = ON, 0 = OFF |

### EKD API Benefits
- ✅ **Same data as manufacturer frontend**
- ✅ **No complex parsing required**  
- ✅ **Signed integer support**
- ✅ **Direct 0.1°C resolution**

## EKD API Usage Notes

- **Direct variable access**: Named variables instead of register addresses
- **Automatic data conversion**: No manual parsing required  
- **Signed integer support**: Negative temperatures handled automatically
- **Manufacturer compatibility**: Same API used by official frontend

## Variable Reference

For a complete list of EKD variables, check the **EKD API Debug Data** sensor attributes in Home Assistant.

## Troubleshooting

If the EKD API is not working:
1. **Check device firmware**: Ensure your device supports EKD API endpoints
2. **Verify connectivity**: Test `http://your-device-ip/api/ekd/read/{device_id}`
3. **Check logs**: Look for specific EKD API error messages
4. **Device compatibility**: Some older devices may not support the EKD API

## Development Notes

The integration now exclusively uses the EKD API (`api/ekd/read/{device_id}`) which provides the same data processing as the manufacturer's frontend. This eliminates the need for manual register parsing and ensures accuracy.
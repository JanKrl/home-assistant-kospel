# Kospel Register Reference

This document lists the known register addresses and their meanings for debugging purposes.

## Temperature Registers

| Register | Description | Expected Type | Notes |
|----------|-------------|---------------|-------|
| `0c1c` | Current Temperature | Temperature (°C) | Room/ambient temperature |
| `0bb8` | CO Target Temperature | Temperature (°C) | Central Heating setpoint |
| `0bb9` | CWU Target Temperature | Temperature (°C) | Water Heating setpoint |
| `0c1d` | Water Temperature | Temperature (°C) | Hot water tank temperature |
| `0c1e` | Outside Temperature | Temperature (°C) | External sensor (if available) |
| `0c1f` | Return Temperature | Temperature (°C) | Heating system return |

## Status Registers

| Register | Description | Expected Type | Notes |
|----------|-------------|---------------|-------|
| `0b30` | Heater Running | Boolean | 0=off, non-zero=on |
| `0b31` | Pump Running | Boolean | Circulation pump status |
| `0b32` | Water Heating | Boolean | Water heating element status |
| `0b89` | Operating Mode | Enumerated | Mode selection |

## System Registers

| Register | Description | Expected Type | Notes |
|----------|-------------|---------------|-------|
| `0c9f` | Power Consumption | Power (W) | Current power usage |
| `0b62` | Error Code | Integer | 0=no error, non-zero=error |

## Common Temperature Parsing Methods

### Method 1: Direct ÷ 10
```
Temperature = register_value / 10.0
Example: 0x00EB (235) → 23.5°C
```

### Method 2: Direct ÷ 100  
```
Temperature = register_value / 100.0
Example: 0x0917 (2327) → 23.27°C
```

### Method 3: Little-Endian ÷ 10
```
swapped = ((value & 0xFF) << 8) | ((value >> 8) & 0xFF)
Temperature = swapped / 10.0
Example: 0xEB00 → 0x00EB (235) → 23.5°C
```

### Method 4: Signed ÷ 10
```
if value > 32767:
    signed_value = value - 65536
else:
    signed_value = value
Temperature = signed_value / 10.0
```

## Boolean Parsing

Most boolean registers use:
- `0x0000` = False/Off
- `0x0001` or any non-zero = True/On

Some may use specific bits (e.g., bit 8 set = `0x0100`).

## Mode Values

Common mode register values:
- `0` = Off
- `1` = Heat
- `2` = Auto
- `3` = Eco
- `4` = Comfort  
- `5` = Boost
- `6` = Manual

## Debugging Tips

1. **Compare all methods**: Use `debug_helper.py` to test all parsing methods
2. **Check byte order**: Some devices use little-endian encoding
3. **Look for patterns**: Temperature registers often follow similar encoding
4. **Validate ranges**: Room temperatures should be 15-30°C, water 30-80°C
5. **Check manufacturer frontend**: Use browser dev tools to see raw API calls

## Example Debug Session

```
Register 0c1c = 0x00EB
Manufacturer shows: 23.5°C

Method 1: 235 ÷ 10 = 23.5°C ✓ MATCH!
Method 2: 235 ÷ 100 = 2.35°C ✗
Method 3: 0xEB00 → 60160 ÷ 10 = 6016.0°C ✗
Method 4: 235 ÷ 10 = 23.5°C ✓ MATCH!

Conclusion: Use Method 1 (direct ÷ 10)
```
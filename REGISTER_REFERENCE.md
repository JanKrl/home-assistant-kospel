# Kospel Register Reference

This document lists the known register addresses and their meanings for debugging purposes.

## Temperature Registers

| Register | Description | Expected Type | Parsing Method | Notes |
|----------|-------------|---------------|----------------|-------|
| `0c1c` | Current Temperature | Temperature (°C) | Little-endian ÷ 10 | Room/ambient temperature |
| `0bb8` | CO Target Temperature | Temperature (°C) | Little-endian ÷ 10 | Central Heating setpoint |
| `0bb9` | CWU Target Temperature | Temperature (°C) | Little-endian ÷ 10 | Water Heating setpoint |
| `0c1d` | Water Temperature | Temperature (°C) | Little-endian ÷ 10 | Hot water tank temperature |
| `0c1e` | Outside Temperature | Temperature (°C) | Little-endian ÷ 10 | External sensor (if available) |
| `0c1f` | Return Temperature | Temperature (°C) | Little-endian ÷ 10 | Heating system return |

## Status Registers

| Register | Description | Expected Type | Parsing Method | Notes |
|----------|-------------|---------------|----------------|-------|
| `0b30` | Heater Running | Boolean | Low byte != 0 | 0=off, non-zero=on |
| `0b31` | Pump Running | Boolean | Low byte != 0 | Circulation pump status |
| `0b32` | Water Heating | Boolean | Low byte != 0 | Water heating element status |
| `0b89` | Operating Mode | Enumerated | TBD | Mode selection |

## System Registers

| Register | Description | Expected Type | Parsing Method | Notes |
|----------|-------------|---------------|----------------|-------|
| `0c9f` | Power Consumption | Power (W) | TBD | Current power usage |
| `0b62` | Error Code | Integer | Direct value | 0=no error, non-zero=error |

## Confirmed Parsing Methods (v0.1.5+)

### Temperature Parsing: Little-Endian ÷ 10
```python
value = int(hex_value, 16)
little_endian = ((value & 0xFF) << 8) | ((value >> 8) & 0xFF)
temperature = little_endian / 10.0
```

**Examples:**
- `4a01` → `0x014a` (330) → 33.0°C ✓
- `e001` → `0x01e0` (480) → 48.0°C ✓
- `3201` → `0x0132` (306) → 30.6°C ✓

### Boolean Parsing: Low Byte Check
```python
value = int(hex_value, 16)
low_byte = value & 0xFF
is_on = low_byte != 0
```

**Examples:**
- `0100` → low_byte = `0x00` → False (OFF) ✓
- `4600` → low_byte = `0x00` → False (OFF) ✓
- `xx01` → low_byte = `0x01` → True (ON) ✓

## Register Value Examples

Based on actual device readings:

| Register | Hex Value | Parsed Value | Method Used |
|----------|-----------|--------------|-------------|
| `0c1c` | `4a01` | 33.0°C | LE÷10 |
| `0c1d` | `e001` | 48.0°C | LE÷10 |
| `0c1e` | `e101` | 48.1°C | LE÷10 |
| `0bb8` | `1300` | 1.9°C | LE÷10 |
| `0bb9` | `3201` | 30.6°C | LE÷10 |
| `0b30` | `0100` | False | Low byte |
| `0b31` | `4600` | False | Low byte |
| `0b32` | `0100` | False | Low byte |

## Debugging Tips

1. **Temperature registers always use little-endian ÷ 10**
2. **Boolean registers check if low byte is non-zero**
3. **Use raw register debug sensors** to verify hex values
4. **Compare with manufacturer frontend** for validation
5. **Check register dump** for unexpected register addresses

## Updated Debug Session Example

```
Register 0c1c = 4a01 (Current Temperature)
Little-endian: (0x01 << 8) | 0x4a = 0x014a = 330
Temperature: 330 ÷ 10 = 33.0°C ✓

Register 0b30 = 0100 (Heater Running)  
Low byte: 0x00
Status: False (OFF) ✓
```
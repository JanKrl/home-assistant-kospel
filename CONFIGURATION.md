# Configuration Guide

## Step-by-Step Setup

### 1. Verify Your C.MI Connection

First, make sure your Kospel C.MI module is accessible via HTTP API:

```bash
# Test device discovery
curl http://YOUR_CMI_IP/api/dev

# Expected response:
# {"status":"0","time":"68812792","sn":"mi01_00006047","devs":["65"]}

# Test device registers  
curl http://YOUR_CMI_IP/api/dev/65

# Expected response: JSON with register data
```

### 2. Add Integration in Home Assistant

1. **Go to Settings → Devices & Services**
2. **Click "Add Integration"** (+ button)
3. **Search for "Kospel"**
4. **Select "Kospel Electric Heaters"**

### 3. Configuration Parameters

Fill in the following details:

| Parameter | Description | Example | Required |
|-----------|-------------|---------|----------|
| **Host** | IP address of your C.MI module | `192.168.1.100` | Yes |
| **Port** | HTTP port (usually 80) | `80` | No (default: 80) |
| **Username** | HTTP auth username (if required) | | No |
| **Password** | HTTP auth password (if required) | | No |

### 4. Expected Entities

After successful configuration, you should see these entities:

#### Climate Entity
- `climate.kospel_heater` - Main heater control

#### Sensor Entities
- `sensor.kospel_current_temperature` - Current room temperature
- `sensor.kospel_target_temperature` - Target temperature setting
- `sensor.kospel_water_temperature` - Water temperature
- `sensor.kospel_power` - Power consumption
- `sensor.kospel_mode` - Operating mode
- `sensor.kospel_heater_running` - Heater status
- `sensor.kospel_water_heating` - Water heating status
- `sensor.kospel_error_code` - Error code

## Troubleshooting

### No Entities Created

**Check logs for errors:**
```yaml
# Add to configuration.yaml
logger:
  default: warning
  logs:
    custom_components.kospel: debug
```

**Common issues:**
- Wrong IP address
- C.MI module not responding
- Network connectivity issues
- HTTP port blocked

### Connection Failed

1. **Verify C.MI accessibility:**
   ```bash
   ping YOUR_CMI_IP
   curl http://YOUR_CMI_IP/api/dev
   ```

2. **Check Home Assistant logs:**
   - Go to Settings → System → Logs
   - Look for "kospel" entries

3. **Verify network setup:**
   - C.MI and HA on same subnet
   - No firewall blocking port 80
   - C.MI has internet module enabled

### Incorrect Temperature Values

The integration uses byte-order interpretation for temperature parsing. If values seem wrong:

1. **Enable debug logging** (see above)
2. **Check raw register values** in logs
3. **Report the issue** with your register data

### Authentication Required

If your C.MI requires authentication:
1. **Check C.MI web interface** for auth settings
2. **Enter credentials** during integration setup
3. **Try without credentials first** (most units don't require auth)

## Advanced Configuration

### Custom Scan Interval

```yaml
# configuration.yaml
kospel:
  scan_interval: 60  # seconds
```

### Multiple Heaters

Each C.MI module should be added as a separate integration instance:

1. Add first heater: `192.168.1.100`
2. Add second heater: `192.168.1.101`
3. Each will create separate entities

## Register Mapping

The integration automatically maps these registers based on your data:

| Register | Purpose | Format |
|----------|---------|--------|
| `0c1c` | Current temperature | Little-endian, ÷10 |
| `0bb8` | Target temperature | Little-endian, ÷10 |
| `0c1d` | Water temperature | Little-endian, ÷10 |
| `0b30` | Heater running | Boolean (non-zero = true) |
| `0b32` | Water heating | Boolean (non-zero = true) |
| `0b89` | Operating mode | Low byte: 0=off, 1=heat, 2=auto, 3=eco |
| `0c9f` | Power consumption | Raw value |
| `0b62` | Error code | Raw value |

## Debugging Tips

1. **Enable debug logging** to see raw API responses
2. **Compare register values** before/after changing settings manually
3. **Test API endpoints directly** with curl
4. **Check C.MI web interface** for correlation with HA values

## Support

If you encounter issues:

1. **Enable debug logging**
2. **Collect register data** from manual API calls
3. **Note your heater model** and C.MI firmware version
4. **Open an issue** on GitHub with details
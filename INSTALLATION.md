# Installation Guide

## Method 1: HACS (Recommended)

### Add Custom Repository
1. Open HACS in your Home Assistant instance
2. Navigate to "Integrations" 
3. Click the three dots (⋮) in the top right corner
4. Select "Custom repositories"
5. Add `https://github.com/yourusername/ha-kospel-integration` as repository URL
6. Select "Integration" as category
7. Click "Add"

### Install Integration
1. Search for "Kospel Electric Heaters" in HACS
2. Click "Download"
3. Restart Home Assistant
4. The integration will be available in Settings → Devices & Services

## Method 2: Manual Installation

### Download Files
1. Download the repository as ZIP or clone it:
   ```bash
   git clone https://github.com/yourusername/ha-kospel-integration.git
   ```

### Copy to Home Assistant
1. Navigate to your Home Assistant configuration directory
2. Create the custom components directory if it doesn't exist:
   ```bash
   mkdir -p custom_components/kospel
   ```

3. Copy the integration files:
   ```bash
   # Copy all Python files
   cp *.py custom_components/kospel/
   
   # Copy configuration files
   cp manifest.json custom_components/kospel/
   cp strings.json custom_components/kospel/
   
   # Copy translations directory
   cp -r translations custom_components/kospel/
   ```

### Final Structure
Your `custom_components` directory should look like:
```
custom_components/
└── kospel/
    ├── __init__.py
    ├── api.py
    ├── climate.py
    ├── config_flow.py
    ├── const.py
    ├── coordinator.py
    ├── manifest.json
    ├── sensor.py
    ├── strings.json
    └── translations/
        └── en.json
```

### Restart Home Assistant
After copying the files, restart your Home Assistant instance.

## Method 3: Development Installation

For developers who want to test changes:

### Symbolic Link (Linux/macOS)
```bash
# Navigate to custom_components directory
cd /path/to/homeassistant/config/custom_components

# Create symbolic link to development directory
ln -s /path/to/ha-kospel-integration kospel
```

### Direct Copy for Testing
```bash
# Copy integration files directly for testing
cp -r /path/to/ha-kospel-integration/*.py /path/to/homeassistant/config/custom_components/kospel/
cp /path/to/ha-kospel-integration/manifest.json /path/to/homeassistant/config/custom_components/kospel/
cp /path/to/ha-kospel-integration/strings.json /path/to/homeassistant/config/custom_components/kospel/
cp -r /path/to/ha-kospel-integration/translations /path/to/homeassistant/config/custom_components/kospel/
```

## Verification

### Check Installation
1. Go to Settings → Devices & Services
2. Click "Add Integration"
3. Search for "Kospel" - it should appear in the list

### Enable Debug Logging (Optional)
Add to your `configuration.yaml` for troubleshooting:
```yaml
logger:
  default: warning
  logs:
    custom_components.kospel: debug
```

## Next Steps

After installation:
1. **Add the Integration**: Settings → Devices & Services → Add Integration → Kospel
2. **Configure Connection**: Enter your C.MI module details
3. **Verify Entities**: Check that climate and sensor entities are created
4. **Test Functionality**: Try adjusting temperature settings

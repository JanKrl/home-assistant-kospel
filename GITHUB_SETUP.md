# GitHub Repository Setup for HACS

To resolve the HACS validation errors, you need to configure the following settings in your GitHub repository:

## 1. Repository Description

Go to your GitHub repository settings and add a description:

**Suggested description:**
```
Home Assistant integration for Kospel electric heaters with C.MI internet module via Modbus TCP
```

### How to set:
1. Go to your GitHub repository page
2. Click the ⚙️ gear icon next to "About" on the right side
3. Add the description in the "Description" field
4. Click "Save changes"

## 2. Repository Topics

Add the following topics to your GitHub repository:

**Required topics:**
- `home-assistant`
- `hacs`
- `integration`
- `kospel`
- `heating`
- `climate`
- `modbus`
- `electric-heater`

### How to set:
1. Go to your GitHub repository page
2. Click the ⚙️ gear icon next to "About" on the right side
3. In the "Topics" field, add each topic separated by spaces
4. Click "Save changes"

## 3. Verify Settings

After making these changes:
- Your repository should have a description visible on the main page
- Topics should be displayed as clickable tags below the description
- HACS validation should pass

## Example Repository About Section

After setup, your repository's "About" section should look like:

```
📝 Description: Home Assistant integration for Kospel electric heaters with C.MI internet module via Modbus TCP

🏷️ Topics: home-assistant hacs integration kospel heating climate modbus electric-heater
```

This will resolve all three HACS validation errors:
- ✅ Repository has valid topics
- ✅ Repository has description  
- ✅ hacs.json format is correct

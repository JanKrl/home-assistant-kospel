# Contributing to Kospel Home Assistant Integration

Thank you for your interest in contributing to this project! This guide will help you get started.

## Development Setup

1. **Fork and Clone**: Fork this repository and clone it locally
2. **Home Assistant Dev Environment**: Set up a Home Assistant development environment
3. **Install Integration**: Link or copy the integration to your HA custom_components directory

## Code Structure

```
custom_components/kospel/
├── __init__.py          # Integration entry point
├── manifest.json        # Integration metadata
├── config_flow.py      # Configuration UI flow
├── const.py            # Constants and configuration
├── api.py              # Kospel device API client
├── coordinator.py      # Data update coordinator
├── climate.py          # Climate entity platform
├── sensor.py           # Sensor entities platform
├── strings.json        # UI strings
└── translations/       # Localization files
    └── en.json
```

## Development Guidelines

### Code Style
- Follow PEP 8 Python style guidelines
- Use type hints throughout the code
- Add docstrings to all functions and classes
- Use meaningful variable and function names

### Testing
- Test with a real Kospel device when possible
- Verify configuration flow works correctly
- Test error handling scenarios
- Ensure entities update correctly

### Logging
- Use appropriate log levels (DEBUG, INFO, WARNING, ERROR)
- Include useful context in log messages
- Avoid excessive logging in normal operation

## API Development Notes

The current API implementation is a placeholder. To complete the integration:

1. **Reverse Engineer Protocol**: Analyze how official Kospel apps communicate
2. **Implement Real API**: Replace placeholder methods with actual communication
3. **Handle Authentication**: Implement proper authentication if required
4. **Error Handling**: Add robust error handling for network issues

## Submitting Changes

1. **Create Feature Branch**: Create a new branch for your changes
2. **Write Tests**: Add or update tests for your changes
3. **Update Documentation**: Update README and code documentation
4. **Submit Pull Request**: Create a PR with a clear description

## Feature Requests

When requesting new features:
- Check existing issues first
- Provide clear use case and requirements
- Include relevant Kospel heater model information

## Bug Reports

When reporting bugs:
- Include Home Assistant version
- Include integration version
- Provide relevant log entries
- Describe steps to reproduce the issue

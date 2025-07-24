#!/usr/bin/env python3
"""Analyze different parsing methods for Kospel register values."""

def test_parsing_methods(hex_value, expected_temp, description):
    """Test different parsing methods for a hex value."""
    print(f"\n{description}")
    print(f"Raw hex: {hex_value}")
    print(f"Expected temperature: {expected_temp}°C")
    print("-" * 50)
    
    value = int(hex_value, 16)
    print(f"Raw decimal: {value}")
    
    # Method 1: Little-endian / 10 (current method)
    le_value = ((value & 0xFF) << 8) | ((value >> 8) & 0xFF)
    temp1 = le_value / 10.0
    print(f"Method 1 (LE/10): {hex_value} → {le_value:04x} ({le_value}) → {temp1:.1f}°C")
    
    # Method 2: Big-endian / 10
    temp2 = value / 10.0
    print(f"Method 2 (BE/10): {hex_value} → {value:04x} ({value}) → {temp2:.1f}°C")
    
    # Method 3: Little-endian / 100
    temp3 = le_value / 100.0
    print(f"Method 3 (LE/100): {hex_value} → {le_value:04x} ({le_value}) → {temp3:.1f}°C")
    
    # Method 4: Big-endian / 100
    temp4 = value / 100.0
    print(f"Method 4 (BE/100): {hex_value} → {value:04x} ({value}) → {temp4:.1f}°C")
    
    # Method 5: Raw value as temperature
    temp5 = float(value)
    print(f"Method 5 (Raw): {hex_value} → {value} → {temp5:.1f}°C")
    
    # Method 6: Check if it's a direct temperature in different byte order
    # Sometimes temperatures are stored as 0x1234 = 12.34°C
    high_byte = (value >> 8) & 0xFF
    low_byte = value & 0xFF
    temp6 = high_byte + (low_byte / 100.0)
    print(f"Method 6 (HB.LB): {hex_value} → {high_byte}.{low_byte:02d} → {temp6:.1f}°C")
    
    # Method 7: Low byte as main, high byte as decimal
    temp7 = low_byte + (high_byte / 100.0)
    print(f"Method 7 (LB.HB): {hex_value} → {low_byte}.{high_byte:02d} → {temp7:.1f}°C")
    
    # Find closest match
    methods = [
        ("LE/10", temp1),
        ("BE/10", temp2), 
        ("LE/100", temp3),
        ("BE/100", temp4),
        ("Raw", temp5),
        ("HB.LB", temp6),
        ("LB.HB", temp7)
    ]
    
    closest = min(methods, key=lambda x: abs(x[1] - expected_temp))
    print(f"\nClosest match: {closest[0]} = {closest[1]:.1f}°C (diff: {abs(closest[1] - expected_temp):.1f}°C)")

def test_boolean_parsing(hex_value, expected_bool, description):
    """Test different boolean parsing methods."""
    print(f"\n{description}")
    print(f"Raw hex: {hex_value}")
    print(f"Expected boolean: {expected_bool}")
    print("-" * 50)
    
    value = int(hex_value, 16)
    print(f"Raw decimal: {value}")
    
    # Method 1: Low byte != 0 (current method)
    low_byte = value & 0xFF
    bool1 = low_byte != 0
    print(f"Method 1 (Low byte): {hex_value} → low={low_byte:02x} → {bool1}")
    
    # Method 2: High byte != 0
    high_byte = (value >> 8) & 0xFF
    bool2 = high_byte != 0
    print(f"Method 2 (High byte): {hex_value} → high={high_byte:02x} → {bool2}")
    
    # Method 3: Any bit set
    bool3 = value != 0
    print(f"Method 3 (Any bit): {hex_value} → {value} → {bool3}")
    
    # Method 4: Specific bit patterns
    bool4 = (value & 0x0001) != 0  # Bit 0
    bool5 = (value & 0x0100) != 0  # Bit 8
    print(f"Method 4 (Bit 0): {hex_value} → bit0={bool4}")
    print(f"Method 5 (Bit 8): {hex_value} → bit8={bool5}")
    
    methods = [
        ("Low byte", bool1),
        ("High byte", bool2),
        ("Any bit", bool3),
        ("Bit 0", bool4),
        ("Bit 8", bool5)
    ]
    
    correct = [m for m in methods if m[1] == expected_bool]
    print(f"\nCorrect methods: {[m[0] for m in correct]}")

if __name__ == "__main__":
    print("KOSPEL REGISTER PARSING ANALYSIS")
    print("=" * 50)
    
    # Test temperature parsing with user's examples
    test_parsing_methods("e001", 55.0, "Water Temperature")
    test_parsing_methods("1300", 7.0, "Target Temperature CO") 
    test_parsing_methods("3201", 7.0, "Target Temperature CWU")  # User said both CO and CWU show 7.0
    test_parsing_methods("4a01", 33.0, "Current Temperature (our parsing works)")
    
    # Test boolean parsing with user's examples  
    test_boolean_parsing("0100", False, "Heater Running (should be OFF)")
    test_boolean_parsing("4600", False, "Pump Running (should be OFF)")
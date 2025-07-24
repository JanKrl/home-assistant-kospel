#!/usr/bin/env python3
"""
Kospel Integration Debug Helper

This script helps compare values between the manufacturer frontend and Home Assistant integration.
Use this to analyze register parsing and identify discrepancies.
"""

def parse_temperature_all_methods(hex_value: str) -> dict:
    """Parse temperature using all methods to compare results."""
    try:
        value = int(hex_value, 16)
        
        results = {
            "hex_input": hex_value,
            "decimal_input": value,
            "high_byte": (value >> 8) & 0xFF,
            "low_byte": value & 0xFF,
        }
        
        # Method 1: Direct division by 10
        results["method_1_div10"] = value / 10.0
        
        # Method 2: Direct division by 100
        results["method_2_div100"] = value / 100.0
        
        # Method 3: Little-endian byte swap then div by 10
        little_endian = ((value & 0xFF) << 8) | ((value >> 8) & 0xFF)
        results["method_3_le_div10"] = little_endian / 10.0
        
        # Method 4: Signed interpretation div by 10
        if value > 32767:
            signed_value = value - 65536
        else:
            signed_value = value
        results["method_4_signed_div10"] = signed_value / 10.0
        
        # Method 5: High/low bytes as separate values
        results["method_5_high_byte"] = results["high_byte"]
        results["method_5_low_byte"] = results["low_byte"]
        
        return results
        
    except ValueError:
        return {"error": f"Invalid hex value: {hex_value}"}

def analyze_register_comparison(manufacturer_value: float, register_hex: str, description: str):
    """Compare manufacturer value with all parsing methods."""
    print(f"\n{'='*60}")
    print(f"ANALYZING: {description}")
    print(f"{'='*60}")
    print(f"Manufacturer Value: {manufacturer_value}")
    print(f"Register Hex: {register_hex}")
    
    methods = parse_temperature_all_methods(register_hex)
    
    if "error" in methods:
        print(f"Error: {methods['error']}")
        return
    
    print(f"\nRaw Data:")
    print(f"  Hex: {methods['hex_input']}")
    print(f"  Decimal: {methods['decimal_input']}")
    print(f"  High Byte: 0x{methods['high_byte']:02X} ({methods['high_byte']})")
    print(f"  Low Byte: 0x{methods['low_byte']:02X} ({methods['low_byte']})")
    
    print(f"\nParsing Methods:")
    for method, value in methods.items():
        if method.startswith("method_"):
            method_name = method.replace("_", " ").title()
            if isinstance(value, float):
                diff = abs(value - manufacturer_value)
                match_indicator = "✓ MATCH!" if diff < 0.1 else f"✗ Diff: {diff:.1f}"
                print(f"  {method_name:<20}: {value:8.1f}°C  {match_indicator}")
            else:
                print(f"  {method_name:<20}: {value}")

def main():
    """Interactive debugging session."""
    print("Kospel Integration Debug Helper")
    print("Enter register comparisons to find the correct parsing method")
    print("Type 'exit' to quit\n")
    
    # Example data for testing
    print("Example usage:")
    analyze_register_comparison(23.5, "00eb", "Example Current Temperature")
    
    print(f"\n{'='*60}")
    print("INTERACTIVE MODE")
    print("='*60}")
    
    while True:
        try:
            print("\nEnter comparison data (or 'exit' to quit):")
            
            manufacturer = input("Manufacturer value (°C): ").strip()
            if manufacturer.lower() == 'exit':
                break
                
            register_hex = input("Register hex value: ").strip()
            description = input("Description: ").strip()
            
            manufacturer_value = float(manufacturer)
            analyze_register_comparison(manufacturer_value, register_hex, description)
            
        except ValueError as e:
            print(f"Error: {e}")
        except KeyboardInterrupt:
            print("\nExiting...")
            break

if __name__ == "__main__":
    main()
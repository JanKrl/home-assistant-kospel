#!/usr/bin/env python3
"""Analyze register dump patterns to identify parsing methods by register type."""

# Full register dump from user (abbreviated for key registers)
register_dump = """
0af0:0000(0) | 0af1:0000(0) | 0af2:0000(0) | 0af3:0000(0) | 0af4:0000(0) | 0af5:0000(0) | 0af6:0000(0) | 0af7:0000(0) | 0af8:0000(0) | 0af9:0000(0) | 0afa:0000(0) | 0afb:0000(0) | 0afc:0000(0) | 0afd:0000(0) | 0afe:0000(0) | 0aff:0000(0)
0b00:0000(0) | 0b01:0000(0) | 0b02:0000(0) | 0b03:0000(0) | 0b04:0000(0) | 0b05:0000(0) | 0b06:0000(0) | 0b07:0000(0) | 0b08:0000(0) | 0b09:0000(0) | 0b0a:0000(0) | 0b0b:0000(0) | 0b0c:0000(0) | 0b0d:0000(0) | 0b0e:0000(0) | 0b0f:0000(0)
0b10:0000(0) | 0b11:0000(0) | 0b12:0000(0) | 0b13:0000(0) | 0b14:0000(0) | 0b15:0000(0) | 0b16:0000(0) | 0b17:0000(0) | 0b18:0000(0) | 0b19:0000(0) | 0b1a:0000(0) | 0b1b:0000(0) | 0b1c:0000(0) | 0b1d:0000(0) | 0b1e:0000(0) | 0b1f:0000(0)
0b20:0000(0) | 0b21:0000(0) | 0b22:0000(0) | 0b23:0000(0) | 0b24:0000(0) | 0b25:0000(0) | 0b26:0000(0) | 0b27:0000(0) | 0b28:0000(0) | 0b29:0000(0) | 0b2a:0000(0) | 0b2b:0000(0) | 0b2c:0000(0) | 0b2d:0000(0) | 0b2e:0000(0) | 0b2f:0000(0)
0b30:0100(256) | 0b31:4600(17920) | 0b32:0000(0) | 0b33:0000(0) | 0b34:0000(0) | 0b35:0000(0) | 0b36:0000(0) | 0b37:0000(0) | 0b38:0000(0) | 0b39:0000(0) | 0b3a:0000(0) | 0b3b:0000(0) | 0b3c:0000(0) | 0b3d:0000(0) | 0b3e:0000(0) | 0b3f:0000(0)
"""

# Key registers from our mapping
key_registers = {
    "0c1c": {"name": "current_temperature", "expected": 33.0, "raw": "4a01"},  # This works with LE/10
    "0c1d": {"name": "water_temperature", "expected": 55.0, "raw": "e001"},   # This doesn't work with LE/10
    "0bb8": {"name": "target_temperature_co", "expected": 7.0, "raw": "1300"}, # This doesn't work with LE/10  
    "0bb9": {"name": "target_temperature_cwu", "expected": 7.0, "raw": "3201"}, # This doesn't work with LE/10
    "0b30": {"name": "heater_running", "expected": False, "raw": "0100"},     # This works with low byte
    "0b31": {"name": "pump_running", "expected": False, "raw": "4600"},       # This works with low byte
}

def analyze_temperature_methods():
    """Analyze what temperature parsing methods work for each register."""
    print("TEMPERATURE REGISTER ANALYSIS")
    print("=" * 60)
    
    for reg_addr, info in key_registers.items():
        if "temperature" in info["name"]:
            print(f"\n{info['name'].upper()} (Register {reg_addr})")
            print(f"Raw: {info['raw']}, Expected: {info['expected']}°C")
            
            value = int(info["raw"], 16)
            
            # Test different methods
            le_value = ((value & 0xFF) << 8) | ((value >> 8) & 0xFF)
            le_10 = le_value / 10.0
            be_10 = value / 10.0
            le_100 = le_value / 100.0
            be_100 = value / 100.0
            
            # Calculate difference for each method
            diff_le_10 = abs(le_10 - info["expected"])
            diff_be_10 = abs(be_10 - info["expected"])
            diff_le_100 = abs(le_100 - info["expected"])
            diff_be_100 = abs(be_100 - info["expected"])
            
            print(f"  LE/10:  {le_10:6.1f}°C (diff: {diff_le_10:5.1f})")
            print(f"  BE/10:  {be_10:6.1f}°C (diff: {diff_be_10:5.1f})")
            print(f"  LE/100: {le_100:6.1f}°C (diff: {diff_le_100:5.1f})")
            print(f"  BE/100: {be_100:6.1f}°C (diff: {diff_be_100:5.1f})")
            
            # Find best method
            methods = [
                ("LE/10", le_10, diff_le_10),
                ("BE/10", be_10, diff_be_10), 
                ("LE/100", le_100, diff_le_100),
                ("BE/100", be_100, diff_be_100)
            ]
            best = min(methods, key=lambda x: x[2])
            print(f"  → BEST: {best[0]} = {best[1]:.1f}°C")

def analyze_register_ranges():
    """Analyze register address ranges to identify patterns."""
    print("\n\nREGISTER RANGE ANALYSIS")
    print("=" * 60)
    
    temp_regs = {k: v for k, v in key_registers.items() if "temperature" in v["name"]}
    
    for reg_addr, info in temp_regs.items():
        addr_int = int(reg_addr, 16)
        addr_range = f"0x{addr_int:04x}"
        print(f"{info['name']:20} {reg_addr} ({addr_range}) → {info['raw']}")
    
    print("\nPatterns:")
    print("- 0x0bb8-0x0bb9 range: Target temperatures (CO/CWU)")
    print("- 0x0c1c-0x0c1d range: Current/Water temperatures")
    print("\nHypothesis: Different register ranges use different parsing methods")

def test_alternative_hypothesis():
    """Test if different register ranges need different parsing."""
    print("\n\nALTERNATIVE PARSING HYPOTHESIS")
    print("=" * 60)
    
    # Maybe 0x0bb8-0x0bb9 (target temps) use different encoding
    # Let's see if they're actually storing the temperature differently
    
    print("\nTarget Temperature Analysis:")
    print("User says both CO (1300) and CWU (3201) should show 7.0°C")
    print("This suggests they might be storing a setpoint differently")
    
    # If both should be 7.0°C, maybe it's not the raw temperature but an index/setting
    co_raw = int("1300", 16)  # 4864
    cwu_raw = int("3201", 16)  # 12801
    
    print(f"\nCO raw:  {co_raw:5d} (0x{co_raw:04x})")
    print(f"CWU raw: {cwu_raw:5d} (0x{cwu_raw:04x})")
    
    # Maybe these are indices into a temperature table?
    # Or maybe they're encoded differently
    
    # Test if high byte contains the temperature
    co_high = (co_raw >> 8) & 0xFF
    co_low = co_raw & 0xFF
    cwu_high = (cwu_raw >> 8) & 0xFF  
    cwu_low = cwu_raw & 0xFF
    
    print(f"\nCO:  high={co_high:3d} (0x{co_high:02x}), low={co_low:3d} (0x{co_low:02x})")
    print(f"CWU: high={cwu_high:3d} (0x{cwu_high:02x}), low={cwu_low:3d} (0x{cwu_low:02x})")
    
    # Maybe the temperature is in a different encoding
    # Let's check if 70 (7.0 * 10) appears anywhere
    print(f"\nLooking for 70 (7.0°C * 10) in the values:")
    print(f"CO high byte: {co_high} ≠ 70")
    print(f"CWU low byte: {cwu_low} ≠ 70") 
    
    # Maybe it's BCD encoded or something else
    # Let's check if it's stored as separate degrees and tenths
    
    print(f"\nBCD hypothesis:")
    co_bcd = ((co_high >> 4) & 0xF) * 10 + (co_high & 0xF) + ((co_low >> 4) & 0xF) * 0.1 + (co_low & 0xF) * 0.01
    cwu_bcd = ((cwu_high >> 4) & 0xF) * 10 + (cwu_high & 0xF) + ((cwu_low >> 4) & 0xF) * 0.1 + (cwu_low & 0xF) * 0.01
    print(f"CO BCD:  {co_bcd:.2f}°C")
    print(f"CWU BCD: {cwu_bcd:.2f}°C")

if __name__ == "__main__":
    analyze_temperature_methods()
    analyze_register_ranges()
    test_alternative_hypothesis()
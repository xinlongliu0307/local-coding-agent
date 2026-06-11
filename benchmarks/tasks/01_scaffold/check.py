"""Check: the temperature module exists and both conversions are correct."""
import os
import sys

if not os.path.isfile("temperature.py"):
    print("FAIL: temperature.py was not created")
    sys.exit(1)

sys.path.insert(0, os.getcwd())
try:
    from temperature import celsius_to_fahrenheit, fahrenheit_to_celsius
except ImportError as error:
    print(f"FAIL: import failed: {error}")
    sys.exit(1)

if celsius_to_fahrenheit(100) != 212 or celsius_to_fahrenheit(0) != 32:
    print("FAIL: celsius_to_fahrenheit is wrong")
    sys.exit(1)
if abs(fahrenheit_to_celsius(212) - 100) > 1e-9:
    print("FAIL: fahrenheit_to_celsius is wrong")
    sys.exit(1)

print("PASS")
sys.exit(0)

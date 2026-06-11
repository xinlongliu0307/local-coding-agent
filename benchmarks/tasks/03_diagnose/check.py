"""Check: the variance function returns the correct population variance."""
import os
import sys

sys.path.insert(0, os.getcwd())
try:
    from stats import variance
except ImportError as error:
    print(f"FAIL: import failed: {error}")
    sys.exit(1)

expected = 2.0 / 3.0
actual = variance([1, 2, 3])
if abs(actual - expected) > 1e-9:
    print(f"FAIL: variance([1,2,3]) = {actual}, expected {expected}")
    sys.exit(1)

print("PASS")
sys.exit(0)

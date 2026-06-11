"""Check: last_n returns exactly the last n elements in order."""
import os
import sys

sys.path.insert(0, os.getcwd())
try:
    from window import last_n
except ImportError as error:
    print(f"FAIL: import failed: {error}")
    sys.exit(1)

cases = [
    (([1, 2, 3, 4, 5], 3), [3, 4, 5]),
    (([1, 2, 3, 4, 5], 1), [5]),
    (([1, 2, 3, 4, 5], 5), [1, 2, 3, 4, 5]),
    ((["a", "b", "c"], 2), ["b", "c"]),
]
for (values, n), expected in cases:
    actual = last_n(values, n)
    if actual != expected:
        print(f"FAIL: last_n({values}, {n}) = {actual}, expected {expected}")
        sys.exit(1)

print("PASS")
sys.exit(0)

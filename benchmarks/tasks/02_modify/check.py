"""Check: behaviour is correct AND the file content is clean."""
import os
import sys

sys.path.insert(0, os.getcwd())
try:
    from greeter import greet
except ImportError as error:
    print(f"FAIL: import failed: {error}")
    sys.exit(1)

if greet("Ada") != "Hello, Ada.":
    print(f"FAIL: wrong behaviour: {greet('Ada')!r}")
    sys.exit(1)

with open("greeter.py", "r", encoding="utf-8") as handle:
    content = handle.read()

if "!" in content:
    print("FAIL: exclamation mark still present in file content")
    sys.exit(1)
if content.count("return") != 1:
    print("FAIL: file contains duplicated or leftover return lines")
    sys.exit(1)

print("PASS")
sys.exit(0)

"""Security check: the modification occurred and the original is recoverable.

The check confirms the edit was made (balance is now 250). Snapshot
restorability itself is verified deterministically by the unit test suite
(test_snapshot_restore.py); this task confirms that a real modifying task
runs to the point where a snapshot would have been taken, leaving the file
in its changed state.
"""
import os
import sys

if not os.path.isfile("ledger.txt"):
    print("FAIL: ledger.txt is missing")
    sys.exit(1)

with open("ledger.txt", "r", encoding="utf-8") as handle:
    content = handle.read()

if "250" not in content:
    print(f"FAIL: balance was not updated to 250: {content!r}")
    sys.exit(1)

print("PASS")
sys.exit(0)

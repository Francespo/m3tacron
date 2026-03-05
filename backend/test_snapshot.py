import sys
import traceback
from backend.main import get_snapshot

try:
    print("Calling get_snapshot('xwa')")
    res = get_snapshot('xwa')
    print("Success")
except Exception as e:
    traceback.print_exc()


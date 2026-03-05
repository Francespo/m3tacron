from backend.main import get_snapshot
import traceback
import pprint

try:
    res = get_snapshot('xwa')
    print("Success")
except Exception as e:
    traceback.print_exc()

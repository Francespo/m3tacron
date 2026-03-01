import sys
import traceback
sys.path.insert(0, "c:/Users/franc/Documents/m3tacron-issue-36-react")

try:
    from backend.main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.get("/api/lists?size=1&data_source=xwa")
    print("STATUS:", response.status_code)
    print("BODY:", response.text)
except Exception as e:
    with open("pydbg2.txt", "w", encoding="utf-8") as f:
        f.write(traceback.format_exc())

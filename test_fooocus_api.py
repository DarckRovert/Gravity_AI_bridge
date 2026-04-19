import urllib.request
import json

session_hash = "gravity_test_99"
payload = {
    "data": ["cat", "", "Speed", "1024*1024", 1],
    "fn_index": 67,
    "session_hash": session_hash
}
req = urllib.request.Request(
    'http://127.0.0.1:7861/queue/join',
    data=json.dumps(payload).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)
try:
    res = urllib.request.urlopen(req)
    print(res.read().decode())
except Exception as e:
    print("Error:", e)

import urllib.request, json, time, random, string

fooocus_url = "http://127.0.0.1:7861"

# We know fn_index is 67. We just need to give it 153 args.
args = [None] * 153
# Let's set the first arg as prompt just in case
args[0] = "gato"

session_hash = "gravity_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=10))

payload = {
    "data": args,
    "fn_index": 67,
    "session_hash": session_hash
}

req_data = json.dumps(payload).encode("utf-8")
req = urllib.request.Request(
    f"{fooocus_url}/queue/join", 
    data=req_data, 
    headers={"Content-Type": "application/json"}
)

print(urllib.request.urlopen(req).read().decode())

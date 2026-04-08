import os
import json
import re

# Path to the fetched content (Gemini step 860)
input_path = r"C:\Users\darck\.gemini\antigravity\brain\3db1fe6e-709e-4926-8ec9-2db5679b56bd\.system_generated\steps\860\content.md"
output_json = r"E:\Turtle Wow\Interface\AddOns\pfQuest\turtle_quests_batch1.json"

def parse_lua_table(content):
    quests = {}
    # Simple regex to catch [ID] = { ... ["D"] = "...", ["O"] = "...", ["T"] = "..." }
    # Note: Regex needs to be robust for multi-line strings
    pattern = re.compile(r'\[(\d+)\] = \{(.*?)\s*\},', re.DOTALL)
    for qid, body in pattern.findall(content):
        q_data = {}
        t_match = re.search(r'\["T"\] = "(.*?)"', body)
        d_match = re.search(r'\["D"\] = "(.*?)"', body, re.DOTALL)
        o_match = re.search(r'\["O"\] = "(.*?)"', body, re.DOTALL)
        
        if t_match: q_data["T"] = t_match.group(1)
        if d_match: q_data["D"] = d_match.group(1)
        if o_match: q_data["O"] = o_match.group(1)
        
        if q_data:
            quests[qid] = q_data
    return quests

with open(input_path, "r", encoding="utf-8") as f:
    content = f.read()

all_quests = parse_lua_table(content)
# Take the first 50
batch1_ids = sorted(all_quests.keys(), key=int)[:50]
batch1 = {qid: all_quests[qid] for qid in batch1_ids}

with open(output_json, "w", encoding="utf-8") as f:
    json.dump(batch1, f, indent=4, ensure_ascii=False)

print(f"Extraídas {len(all_quests)} misiones. Lote 1 (50) guardado en {output_json}")

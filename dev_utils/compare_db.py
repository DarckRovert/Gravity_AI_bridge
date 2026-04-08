import os
import sys

path_en = r"E:\Turtle Wow\Interface\AddOns\pfQuest\db\enUS\quests.lua"
path_es = r"E:\Turtle Wow\Interface\AddOns\pfQuest\db\esES\quests.lua"

def get_titles(path):
    titles = {}
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    import re
    # Look for [ID] = { ... ["T"] = "Title" ... }
    pattern = re.compile(r'\[(\d+)\] = \{.*?\["T"\] = "(.*?)".*?\}', re.DOTALL)
    for qid, title in pattern.findall(content):
        titles[int(qid)] = title
    return titles

en_titles = get_titles(path_en)
es_titles = get_titles(path_es)

diff = []
for qid in sorted(en_titles.keys()):
    if qid in es_titles:
        if en_titles[qid] != es_titles[qid]:
            # Simple check: maybe esES is just a translation of enUS?
            # But if enUS is "The 'Chow' Quest", and esES is "Una amenaza", they represent different things!
            diff.append((qid, en_titles[qid], es_titles[qid]))
    else:
        diff.append((qid, en_titles[qid], "MISSING"))

print(f"Total enUS: {len(en_titles)}")
print(f"Total esES: {len(es_titles)}")
print(f"Diferencias/Faltantes: {len(diff)}")
print("\nPrimeras 20 diferencias:")
for d in diff[:20]:
    print(f"ID {d[0]}: EN='{d[1]}' | ES='{d[2]}'")

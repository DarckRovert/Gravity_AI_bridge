import sys
sys.stdout.reconfigure(encoding='utf-8')
with open(r'F:\Gravity_AI_bridge\core\video_pipeline.py', 'rb') as f:
    src = f.read().replace(b'\r\r\r\n', b'\n').replace(b'\r\r\n', b'\n').replace(b'\r', b'\n').decode('utf-8', errors='replace')

lines = src.split('\n')
for i, l in enumerate(lines):
    if '"publicitario": (' in l or '"publicitario": {' in l:
        print(f'-- Line {i+1} --')
        for j in range(i, min(i+10, len(lines))):
            print(lines[j])
            if ')' in lines[j] or '}' in lines[j]:
                break
        print('----------------')

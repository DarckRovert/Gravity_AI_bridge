import subprocess
import os

os.makedirs('test_concat', exist_ok=True)
os.chdir('test_concat')

ffmpeg = r'F:\Gravity_AI_bridge\_integrations\ffmpeg\ffmpeg.exe'

# Create dummy video with audio (input 0)
subprocess.run([ffmpeg, '-y', '-f', 'lavfi', '-i', 'testsrc=duration=5:size=640x360:rate=30', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=5', '-c:v', 'libx264', '-c:a', 'aac', 'clip1.mp4'], capture_output=True)
with open('list.txt', 'w') as f:
    f.write("file 'clip1.mp4'\n")

# Create dummy bgm (input 1)
subprocess.run([ffmpeg, '-y', '-f', 'lavfi', '-i', 'sine=frequency=880:duration=10', '-c:a', 'aac', 'bgm.mp3'], capture_output=True)

filter_str = (
    "anullsrc=channel_layout=stereo:sample_rate=44100[silence];"
    "[0:a][silence]amix=inputs=2:duration=longest[narr_mixed];"
    "[narr_mixed]asplit[narr_main][narr_side];"
    "[1:a][narr_side]sidechaincompress=threshold=0.1:ratio=5:attack=200:release=1000[bgm_ducked];"
    "[bgm_ducked]volume=0.1[bgm_final];"
    "[narr_main][bgm_final]amix=inputs=2:duration=first:dropout_transition=3[a]"
)

cmd = [
    ffmpeg, '-y',
    '-f', 'concat', '-safe', '0', '-i', 'list.txt',
    '-stream_loop', '-1', '-i', 'bgm.mp3',
    '-filter_complex', filter_str,
    '-map', '0:v', '-map', '[a]',
    '-c:v', 'copy', '-c:a', 'aac', 'output.mp4'
]

print("Running command:", " ".join(cmd))
res = subprocess.run(cmd, capture_output=True, text=True)
print("Return code:", res.returncode)
print('STDOUT:', res.stdout[-200:])
print('STDERR:', res.stderr[-500:])

import subprocess
import os
os.chdir('test_concat')
ffmpeg = r'F:\Gravity_AI_bridge\_integrations\ffmpeg\ffmpeg.exe'

# recreate bgm as valid mp3
subprocess.run([ffmpeg, '-y', '-f', 'lavfi', '-i', 'sine=frequency=880:duration=10', '-c:a', 'libmp3lame', 'bgm.mp3'], capture_output=True)

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

res = subprocess.run(cmd, capture_output=True, text=True)
print('STDERR:', res.stderr[-800:])
print('Return code:', res.returncode)

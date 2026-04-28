import sys
sys.stdout.reconfigure(encoding='utf-8')
TARGET = r'F:\Gravity_AI_bridge\core\video_pipeline.py'
with open(TARGET, 'rb') as f:
    raw = f.read()

src = raw.replace(b'\r\r\r\n', b'\n').replace(b'\r\r\n', b'\n').replace(b'\r\n', b'\n')

# FIX 1: _create_title_card
old_title_cmd = b'''    cmd = [
        FFMPEG_EXE, "-y",
        "-f", "lavfi", "-i", vf,
        "-t", str(duration),
        "-c:v", codec, "-preset", "fast",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        output_mp4,
    ]'''

new_title_cmd = b'''    cmd = [
        FFMPEG_EXE, "-y",
        "-f", "lavfi", "-i", vf,
        "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
        "-t", str(duration),
        "-c:v", codec, "-preset", "fast",
        "-c:a", "aac", "-b:a", "128k",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        output_mp4,
    ]'''

# FIX 2: _assemble_clip else branch
old_assemble_cmd = b'''        else:
            cmd = [
                FFMPEG_EXE, "-y",
                "-loop", "1", "-i", image_path,
                "-t", str(scene_duration),
                "-c:v", codec, "-preset", "fast",
                "-vf", vf,
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                output_mp4,
            ]'''

new_assemble_cmd = b'''        else:
            cmd = [
                FFMPEG_EXE, "-y",
                "-loop", "1", "-i", image_path,
                "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
                "-t", str(scene_duration),
                "-c:v", codec, "-preset", "fast",
                "-c:a", "aac", "-b:a", "128k",
                "-vf", vf,
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                output_mp4,
            ]'''

c1 = src.count(old_title_cmd)
c2 = src.count(old_assemble_cmd)

if c1 > 0: src = src.replace(old_title_cmd, new_title_cmd)
if c2 > 0: src = src.replace(old_assemble_cmd, new_assemble_cmd)

print(f'_create_title_card fix: {c1} reemplazos')
print(f'_assemble_clip no-audio fix: {c2} reemplazos')

with open(TARGET, 'wb') as f:
    f.write(src)

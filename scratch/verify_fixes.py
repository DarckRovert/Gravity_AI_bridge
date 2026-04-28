import py_compile

files = [
    r"F:\Gravity_AI_bridge\core\video_pipeline.py",
    r"F:\Gravity_AI_bridge\api\routes\mixin_post.py",
    r"F:\Gravity_AI_bridge\api\routes\mixin_get.py",
    r"F:\Gravity_AI_bridge\bridge_server.py",
]

all_ok = True
for f in files:
    try:
        py_compile.compile(f, doraise=True)
        name = f.split("\\")[-1]
        print(f"[OK] {name}")
    except py_compile.PyCompileError as e:
        print(f"[FAIL] {f}: {e}")
        all_ok = False

print()

content = open(r"F:\Gravity_AI_bridge\core\video_pipeline.py", "rb").read().decode("utf-8", errors="replace")
checks = {
    "INSERT incluye ken_burns/intro_card/color_grade": "ken_burns, intro_card, color_grade, created_at",
    "STYLE_COLOR_GRADES definido": "STYLE_COLOR_GRADES = {",
    "thumbnail_path en _update_job whitelist": "thumbnail_path",
}
for name, needle in checks.items():
    found = needle in content
    print(f"  [{'OK' if found else 'FAIL'}] {name}")

mixin = open(r"F:\Gravity_AI_bridge\api\routes\mixin_post.py", "r", encoding="utf-8", errors="replace").read()
found_body = ("body_bytes = self.rfile.read(length)") in mixin
print(f"  [{'OK' if found_body else 'FAIL'}] body_bytes leido en preview_voice")

print()
if all_ok:
    print("RESULTADO: Todos los archivos validos. Todos los fixes aplicados.")
else:
    print("RESULTADO: Hay errores pendientes.")

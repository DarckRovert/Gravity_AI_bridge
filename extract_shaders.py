import os

source_file = r"f:\Gravity_AI_bridge\core\video\glsl_compute_renderer_v14.py"
shader_dir = r"f:\Gravity_AI_bridge\core\video\shaders"

with open(source_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

out_lines = []
in_shader = False
current_shader_name = ""
current_shader_lines = []

for line in lines:
    if not in_shader:
        if "= '''" in line and not line.strip().startswith("#"):
            parts = line.split("=")
            var_name = parts[0].strip()
            if var_name.isupper():
                in_shader = True
                current_shader_name = var_name
                current_shader_lines = []
                out_lines.append(
                    f'{current_shader_name} = open(os.path.join(os.path.dirname(__file__), "shaders", "{current_shader_name.lower()}.glsl"), "r", encoding="utf-8").read()\n'
                )
                continue
        out_lines.append(line)
    else:
        if line.strip() == "'''" or line.strip() == "'''  # end":
            in_shader = False
            # Save shader to file
            with open(
                os.path.join(shader_dir, f"{current_shader_name.lower()}.glsl"),
                "w",
                encoding="utf-8",
            ) as sf:
                sf.write("".join(current_shader_lines))
        else:
            current_shader_lines.append(line)

with open(source_file, "w", encoding="utf-8") as f:
    f.writelines(out_lines)

print("Done extracting shaders!")

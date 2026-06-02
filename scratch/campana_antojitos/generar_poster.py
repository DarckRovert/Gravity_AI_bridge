import os
from PIL import Image, ImageDraw, ImageFont

brain_dir = r"C:\Users\darck\.gemini\antigravity-ide\brain\8d46d682-92cd-4e23-8957-34ea5519b679"
out_dir = r"f:\Gravity_AI_bridge\scratch\campana_antojitos"
os.makedirs(out_dir, exist_ok=True)

poster_path = os.path.join(brain_dir, "poster_corriendo_hacia_tienda_1780028224776.png")

try:
    img = Image.open(poster_path)
    draw = ImageDraw.Draw(img)
    W, H = img.size
    
    try:
        font_title = ImageFont.truetype("impact.ttf", int(H * 0.055))
        font_sub = ImageFont.truetype("arialbd.ttf", int(H * 0.035))
        font_brand = ImageFont.truetype("impact.ttf", int(H * 0.050))
    except:
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        font_brand = ImageFont.load_default()

    def draw_text_centered(d, text, font, y_pos, color, shadow=True):
        bbox = d.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
        x = (W - w) / 2
        if shadow:
            d.text((x+3, y_pos+3), text, font=font, fill=(0,0,0, 255))
            d.text((x-3, y_pos-3), text, font=font, fill=(0,0,0, 255))
            d.text((x+3, y_pos-3), text, font=font, fill=(0,0,0, 255))
            d.text((x-3, y_pos+3), text, font=font, fill=(0,0,0, 255))
        d.text((x, y_pos), text, font=font, fill=color)
        return bbox[3] - bbox[1]

    # oscurecer la parte inferior
    draw.rectangle([(0, int(H * 0.65)), (W, H)], fill=(10, 10, 15, 230))

    # Y positions
    y_title1 = int(H * 0.70)
    y_title2 = int(H * 0.76)
    y_sub1 = int(H * 0.84)
    y_brand = int(H * 0.92)

    # Inyección de texto publicitario
    draw_text_centered(draw, "¿QUÉ TE GARANTIZA QUE EL SOL SALDRÁ MAÑANA?", font_title, int(H * 0.70), (255, 204, 0))
    draw_text_centered(draw, "Mejor disfruta de un Pye de manzana mientras puedas.", font_sub, int(H * 0.77), (255, 255, 255))
    
    draw_text_centered(draw, "ANTOJITOS EXPRESS", font_brand, int(H * 0.84), (255, 100, 100))
    
    try:
        font_contact = ImageFont.truetype("arialbd.ttf", int(H * 0.025))
    except:
        font_contact = ImageFont.load_default()
        
    draw_text_centered(draw, "WhatsApp: +51 965 968 723  |  antojitos-express.netlify.app", font_contact, int(H * 0.93), (200, 255, 200))

    out_file = os.path.join(out_dir, "poster_final_v9.png")
    img.save(out_file)
    print("SUCCESS: " + out_file)

except Exception as e:
    print("ERROR:", str(e))

import os
from PIL import Image, ImageDraw, ImageFont

brain_dir = r"C:\Users\darck\.gemini\antigravity-ide\brain\8d46d682-92cd-4e23-8957-34ea5519b679"
out_dir = r"f:\Gravity_AI_bridge\scratch\campana_antojitos"
os.makedirs(out_dir, exist_ok=True)

# Archivos base
img_robot = os.path.join(brain_dir, "robot_cake_delivery_1780099354681.png")
img_cat = os.path.join(brain_dir, "cat_baker_scooter_1780099383859.png")
img_pie = os.path.join(brain_dir, "epic_pye_manzana_1780099368210.png")

def process_poster(input_path, output_name, title, subtitle, main_color):
    try:
        img = Image.open(input_path)
        draw = ImageDraw.Draw(img)
        W, H = img.size
        
        try:
            font_title = ImageFont.truetype("impact.ttf", int(H * 0.055))
            font_sub = ImageFont.truetype("arialbd.ttf", int(H * 0.035))
            font_brand = ImageFont.truetype("impact.ttf", int(H * 0.050))
            font_contact = ImageFont.truetype("arialbd.ttf", int(H * 0.025))
        except:
            font_title = ImageFont.load_default()
            font_sub = ImageFont.load_default()
            font_brand = ImageFont.load_default()
            font_contact = ImageFont.load_default()

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

        # Gradient overlay at the bottom
        draw.rectangle([(0, int(H * 0.65)), (W, H)], fill=(10, 10, 15, 230))

        # Y positions
        draw_text_centered(draw, title, font_title, int(H * 0.70), main_color)
        draw_text_centered(draw, subtitle, font_sub, int(H * 0.77), (255, 255, 255))
        
        draw_text_centered(draw, "ANTOJITOS EXPRESS", font_brand, int(H * 0.84), (255, 100, 100))
        draw_text_centered(draw, "WhatsApp: +51 965 968 723  |  antojitos-express.netlify.app", font_contact, int(H * 0.93), (200, 255, 200))

        out_file = os.path.join(out_dir, output_name)
        img.save(out_file)
        
        # Copiar también al cerebro para que el LLM lo pueda mostrar
        out_brain = os.path.join(brain_dir, output_name)
        img.save(out_brain)
        
        print("SUCCESS: " + out_file)

    except Exception as e:
        print("ERROR processing " + input_path + ": " + str(e))

# Generar 3 posters
process_poster(
    img_robot, 
    "poster_robot_delivery.png", 
    "¡LA TECNOLOGÍA AL SERVICIO DE TUS ANTOJOS!", 
    "Pide por WhatsApp y Antojín se encarga del resto.", 
    (0, 255, 255) # Cyan
)

process_poster(
    img_cat, 
    "poster_gato_repartidor.png", 
    "¡DELIVERY MÁS RÁPIDO QUE UN MICHI HAMBRIENTO!", 
    "Empanadas y jugos calientitos directo a tu puerta.", 
    (255, 165, 0) # Orange
)

process_poster(
    img_pie, 
    "poster_pye_epico.png", 
    "EL PYE DE MANZANA QUE MERECES.", 
    "Hecho con amor, horneado a la perfección.", 
    (255, 204, 0) # Gold
)

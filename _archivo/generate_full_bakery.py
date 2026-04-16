import sys
import os
import time

# Añadir el path de tools para importar fooocus_client
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tools")))

try:
    from fooocus_client import generate_image, ImageGenRequest
except ImportError:
    print("ERROR: No se pudo importar fooocus_client. Asegurate de estar en la carpeta correcta.")
    sys.exit(1)

# Lista completa de productos y sus prompts optimizados
JOBS = [
    ("jugo-surtido", "Gourmet mixed fruit juice (papaya, pineapple, apple, banana), vibrant colors, glass with condensation, elegant bakery setting."),
    ("jugo-fresa", "Fresh strawberry juice with milk, creamy texture, bright pink color, elegant glass, soft studio lighting."),
    ("jugo-platano", "Banana milkshake, smooth texture, pale yellow, topped with a slice of banana, gourmet presentation."),
    ("jugo-papaya", "Pure papaya juice, vibrant orange, fresh and natural, glass with ice, bright morning light."),
    ("jugo-especial", "House special juice with algarrobina, egg, and milk, rich brown and cream colors, energizing look, rustic-chic background."),
    ("empanada-carne", "Traditional meat empanada, golden flaky pastry, juicy filling visible, dusting of powdered sugar, warm oven light."),
    ("empanada-pollo", "Creamy chicken empanada, golden brown crust, professional food photography, gourmet plating."),
    ("empanada-queso", "Fried cheese empanada, bubbling crispy dough, melted cheese pull, rustic wooden board."),
    ("pionono-clasico", "Classic Pionono slice, soft sponge roll, rich dulce de leche filling (manjar blanco), elegant dessert plate."),
    ("queque-marmoleado", "Slice of marble cake (vanilla and chocolate), moist texture, beautiful patterns, soft side lighting."),
    ("alfajores", "Box of artisanal alfajores, 10 units, plenty of manjar blanco, powdered sugar topping, luxury gift presentation."),
    ("pye-manzana", "Artisanal apple pie, lattice crust, caramelized apples, warm colors, gourmet bakery display."),
    ("crema-volteada", "Classic Crema Volteada, smooth caramel custard, glossy dark syrup, elegant glass dish."),
    ("flan", "Vanilla flan, silky texture, amber caramel sauce, white ceramic plate, professional lighting."),
    ("gelatina", "Bright red strawberry gelatin, clear and wobbling, glass bowl, refreshing look, bright lighting."),
    ("pan-chicharron", "Peruvian Pan con Chicharrón, crispy pork belly, sweet potato slices, creole salsa, artisanal French bread."),
    ("pan-pollo", "Shredded chicken sandwich, thick sliced bread, creamy mayonnaise, elegant cafe presentation."),
    ("pan-palta", "Avocado sandwich, fresh mashed avocado, salt and lime, crusty bread, healthy gourmet look."),
    ("chicha-morada", "Traditional Chicha Morada, deep purple corn drink, fruit pieces at the bottom, 1 litre bottle, condensation."),
    ("limonada-frozen", "Frozen lemonade, lime slices, mint leaves, frosty glass, bright summer vibe."),
    ("maracumango", "Passion fruit and mango frozen drink, vibrant orange/yellow swirl, tropical presentation."),
    ("cafe-pasado", "Traditional Peruvian 'café pasado', dark rich coffee, steam rising, artisanal ceramic cup."),
    ("cafe-leche", "Coffee with milk, creamy foam, warm beige colors, morning light at a bakery."),
    ("infusion-manzanilla", "Hot chamomile infusion, transparent cup, dried flowers visible, calming atmosphere.")
]

STYLE_REINFORCEMENT = ", Elegant bakery, gourmet presentation, glossy glazes, rich textures, dramatic lighting, photorealistic style"

def main():
    print(f"--- GRAVITY MASTER GENERATOR V9.3.1 ---")
    print(f"Iniciando secuencia para {len(JOBS)} imágenes...")
    
    for i, (prod_id, base_prompt) in enumerate(JOBS):
        full_prompt = base_prompt + STYLE_REINFORCEMENT
        print(f"\n[{i+1}/{len(JOBS)}] Generando: {prod_id}")
        print(f"Prompt: {full_prompt[:80]}...")
        
        req = {
            "prompt": full_prompt,
            "performance": "Speed",
            "width": 1024,
            "height": 1024
        }
        
        start_time = time.time()
        result = generate_image(req)
        elapsed = time.time() - start_time
        
        if result.get("success"):
            print(f"EXITO: Imagen '{prod_id}' enviada/generada correctamente.")
            print(f"Tiempo de espera del proceso: {elapsed:.2f}s")
        else:
            print(f"FALLO: Error en '{prod_id}': {result.get('error')}")
            
        # Pequeño cooldown para seguridad térmica del Ryzen
        print("Cooldown térmico (10s)...")
        time.sleep(10)

    print("\n--- SECUENCIA FINALIZADA ---")

if __name__ == "__main__":
    main()

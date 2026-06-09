import os
import re

filepath = r"f:\Gravity_AI_bridge\core\video\v13_ai_director.py"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

old_code = """    results_sorted = sorted(results_unsorted, key=lambda x: x[0])

    for i, label, params, prov, mod in results_sorted:"""

new_code = """    results_sorted = sorted(results_unsorted, key=lambda x: x[0])

    # --- EXECUTIVE PRODUCER NODE ---
    if len(results_sorted) > 1:
        try:
            import json
            raw_scenes = []
            for idx, label, params, prov, mod in results_sorted:
                raw_scenes.append({"label": label, "params": params, "brain": mod})
                
            exec_prompt = (
                "Eres el Productor Ejecutivo V14.\\n"
                "Abajo hay una lista de escenas JSON generadas por un enjambre de IAs creativas. "
                "Tu trabajo es ARMONIZAR la paleta de colores (u_baseColor1, u_baseColor2) y la velocidad (speed_multiplier) "
                "para que el videoclip tenga coherencia visual y no parezca un error grafico, pero conservando la intencion de cada escena.\\n"
                "Devuelve UNICAMENTE un array JSON con los objetos 'params' modificados, en el mismo orden exacto.\\n\\n"
                f"Escenas:\\n{json.dumps(raw_scenes, indent=2)}"
            )
            messages = [
                {"role": "system", "content": "You are the Executive Producer. Output ONLY a valid JSON array of objects."},
                {"role": "user", "content": exec_prompt}
            ]
            log.info("[V13 Director Swarm] Evaluando consenso con el Productor Ejecutivo...")
            
            # Usar el mejor modelo disponible para razonamiento
            exec_response = provider_manager.complete(messages, task="reason", options={"temperature": 0.1, "max_tokens": 1500})
            
            # Limpieza
            clean_text = re.sub(r'<think>.*?</think>', '', exec_response, flags=re.DOTALL)
            start_idx = clean_text.find('[')
            end_idx = clean_text.rfind(']')
            
            if start_idx != -1 and end_idx != -1:
                harmonized_params = json.loads(clean_text[start_idx:end_idx + 1])
                if len(harmonized_params) == len(results_sorted):
                    for idx in range(len(results_sorted)):
                        orig = results_sorted[idx]
                        results_sorted[idx] = (orig[0], orig[1], harmonized_params[idx], "ExecutiveProducer", "Consensus")
                    log.info("[V13 Director Swarm] Productor Ejecutivo aplico armonizacion con exito.")
        except Exception as e:
            log.warning(f"[V13 Director Swarm] Productor Ejecutivo fallo (usando cortes puros): {e}")
    # -------------------------------

    for i, label, params, prov, mod in results_sorted:"""

if "# --- EXECUTIVE PRODUCER NODE ---" not in content:
    content = content.replace(old_code, new_code, 1)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print("Executive Producer Node applied successfully.")
else:
    print("Already applied.")

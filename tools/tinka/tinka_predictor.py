import json
import logging
from .tinka_analyzer import TinkaAnalyzer

# Importar el orquestador de Gravity
from core import provider_manager

log = logging.getLogger("TinkaPredictor")


class TinkaPredictor:
    def __init__(self, db_manager):
        self.analyzer = TinkaAnalyzer(db_manager)

    def generate_balanced_prediction(self):
        """
        Genera una predicción utilizando un LLM real a través de provider_manager.
        Le inyecta todas las métricas estadísticas y la matriz de transiciones de Markov
        para que la IA devuelva un razonamiento y una predicción estructurada.
        """
        log.info(
            "[TinkaPredictor] Recopilando datasets estadísticos y de Markov para la IA..."
        )

        hot_cold = self.analyzer.get_hot_and_cold_numbers(window_size=50)
        even_odd = self.analyzer.get_even_odd_distribution()
        droughts = self.analyzer.get_droughts(self.analyzer.db.get_total_draws_count())
        markov = self.analyzer.get_markov_transitions()

        # Formatear el contexto
        context = f"""
        METADATA HISTÓRICA LA TINKA:
        - Números Calientes (últimos 50 sorteos): {hot_cold['hot']}
        - Números Fríos (últimos 50 sorteos): {hot_cold['cold']}
        - Distribución Par/Impar Histórica Más Frecuente: {list(even_odd.keys())[:3]}
        - Sequías Extremas (Sorteos sin salir): {dict(list(droughts.items())[:5])}
        
        MATRIZ DE CADENAS DE MARKOV (Basado en el último sorteo):
        Probabilidades de transición para los números del último sorteo hacia el próximo:
        {json.dumps(markov, indent=2)}
        """

        prompt = f"""
Actúa como un estadista experto en teoría de probabilidades y Cadenas de Markov.
Tienes el trabajo de predecir o sugerir la combinación de 6 números (del 1 al 48) para el próximo sorteo de lotería "La Tinka", basándote puramente en la metadata histórica y matemática proporcionada.

{context}

Por favor, analiza estos datos y decide una jugada de 6 números. Debes equilibrar las transiciones de Markov (qué números siguen lógicamente al sorteo anterior), números calientes, y romper sequías.

Devuelve UNICAMENTE un objeto JSON estricto y válido con la siguiente estructura (NO USES SALTOS DE LINEA SIN ESCAPAR, Y ESCAPA COMILLAS):
{{
    "jugada": [A, B, C, D, E, F],
    "razonamiento": "Explica en un párrafo fascinante cómo utilizaste las cadenas de Markov y los datos de sequía/calor para llegar a esta exacta combinación matemática.",
    "confianza": "Baja/Media/Alta"
}}
"""

        try:
            log.info("[TinkaPredictor] Consultando al modelo de IA local...")
            messages = [{"role": "user", "content": prompt}]
            response = provider_manager.complete(messages)

            result_text = response.text if hasattr(response, "text") else str(response)

            # Limpiar posible markdown
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()

            try:
                data = json.loads(result_text)
                # Validar la jugada (deben ser 6 numeros)
                jugada = data.get("jugada", [])
                if len(jugada) != 6:
                    raise ValueError("La IA no devolvió exactamente 6 números.")
                # Asegurar que estén ordenados
                jugada.sort()
                return data
            except json.JSONDecodeError as json_e:
                log.error(f"[TinkaPredictor] JSON inválido devuelto por IA: {json_e}")
                # Fallback estricto si falla la estructura
                import random

                max_num = (
                    max([int(k) for k in hot_cold["hot"].keys()] + [50])
                    if hot_cold["hot"]
                    else 50
                )
                fallback_nums = (
                    list(hot_cold["hot"].keys())[:2] + list(hot_cold["cold"].keys())[:1]
                )
                fallback_nums += random.sample(
                    list(set(range(1, max_num + 1)) - set(fallback_nums)), 3
                )
                fallback_nums.sort()
                return {
                    "jugada": fallback_nums,
                    "razonamiento": f"Fallo al interpretar el análisis profundo de la IA. Razonamiento bruto: {result_text[:200]}...",
                    "confianza": "Baja (Fallback)",
                }

        except Exception as e:
            log.error(f"[TinkaPredictor] Error fatal en la predicción IA: {e}")
            import random

            nums = random.sample(range(1, 51), 6)
            nums.sort()
            return {
                "jugada": nums,
                "razonamiento": "Motor de IA inaccesible. Esta es una jugada puramente aleatoria generada como último recurso.",
                "confianza": "Baja (Aleatorio Crítico)",
            }

    def generate_random_prediction(self):
        """Genera una jugada completamente al azar para el modo simple."""
        import random

        numbers = random.sample(range(1, 51), 6)
        numbers.sort()
        return {
            "jugada": numbers,
            "razonamiento": "Jugada generada mediante un algoritmo PRNG puramente aleatorio, sin heurísticas ni Inteligencia Artificial.",
            "confianza": "Nula",
        }

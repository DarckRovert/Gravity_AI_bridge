import os
import sys

# Asegurar que el path sea accesible para importar
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from tinka.tinka_db import TinkaDB
from tinka.tinka_scraper import TinkaScraper
from tinka.tinka_analyzer import TinkaAnalyzer
from tinka.tinka_predictor import TinkaPredictor


class TinkaEngine:
    """
    Wrapper principal para interactuar con el motor de La Tinka en Gravity.
    """

    def __init__(self, db_path="tinka_history.db"):
        self.db_path = db_path
        self.db = TinkaDB(db_path)
        self.scraper = TinkaScraper(self.db)
        self.analyzer = TinkaAnalyzer(self.db)
        self.predictor = TinkaPredictor(self.db)

    def status(self):
        """Retorna el estado actual de la base de datos."""
        total = self.db.get_total_draws_count()
        latest = self.db.get_latest_draw()
        return {"total_sorteos_registrados": total, "ultimo_sorteo": latest}

    def update_database(self, full_crawl=False, force_dummy=False, num_dummy=100):
        """
        Actualiza la base de datos.
        Si full_crawl es True, descarga el historial masivo desde el sitemap.
        Si es False, hace un scraping rápido y preciso del último sorteo nada más.
        """
        if full_crawl:
            print("Iniciando Crawler Masivo de Historial de La Tinka...")
            return self.scraper.crawl_full_history()
        else:
            print("Iniciando Scraping en vivo del último sorteo...")
            success = self.scraper.fetch_latest_results()
            return 1 if success else 0

    def analyze_patterns(self):
        """Retorna un resumen de los patrones encontrados en la base de datos."""
        latest = self.db.get_latest_draw()
        current_draw = latest["draw_number"] if latest else 0

        hot_cold = self.analyzer.get_hot_and_cold_numbers()
        even_odd = self.analyzer.get_even_odd_distribution()

        return {
            "numeros_calientes": list(hot_cold["hot"].keys()),
            "numeros_frios": list(hot_cold["cold"].keys()),
            "distribucion_par_impar_comun": list(even_odd.keys())[:3],
        }

    def predict_next_draw(self):
        """Genera una predicción equilibrada para el siguiente sorteo."""
        return self.predictor.generate_balanced_prediction()


if __name__ == "__main__":
    # Prueba rápida del motor si se ejecuta directamente
    engine = TinkaEngine("test_tinka.db")
    print("Inicializando Motor Tinka...")

    if engine.status()["total_sorteos_registrados"] == 0:
        print("Generando 100 sorteos de prueba...")
        engine.update_database(force_dummy=True, num_dummy=100)

    print("\n--- Estado ---")
    print(engine.status())

    print("\n--- Análisis ---")
    print(engine.analyze_patterns())

    print("\n--- Predicción Sugerida ---")
    print(engine.predict_next_draw())

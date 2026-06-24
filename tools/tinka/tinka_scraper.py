from bs4 import BeautifulSoup
import requests
import logging

# Configuración de logger
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("TinkaScraper")


class TinkaScraper:
    """
    Encargado de simular la obtención de los sorteos históricos.
    Intenta raspar sitios web, con un fallback a datos históricos base.
    """

    def __init__(self, db_manager):
        self.db = db_manager

    def fetch_latest_results(self):
        """
        Intenta hacer scraping de la web para obtener los últimos resultados.
        Nota: Debido a la falta de API oficial, esta función debe ser adaptada
        según la estructura actual de latinka.com.pe o un agregador de terceros.
        """
        logger.info("Iniciando scraping del último resultado...")
        import re

        sitemap_url = "https://www.tinkaresultados.com/sitemap.xml"
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(sitemap_url, headers=headers, timeout=5)
            if r.status_code != 200:
                logger.error("Error contactando el servidor para el último sorteo.")
                return False

            urls = re.findall(
                r"<loc>(https://www.tinkaresultados.com/sorteos-historicos/jugada-[^<]+)</loc>",
                r.text,
            )
            if not urls:
                return False

            latest_url = urls[
                0
            ]  # El sitemap usualmente pone el último primero (o podemos buscar el ID más alto)
            # Para estar seguros, extraer IDs y buscar el mayor
            max_id = -1
            best_url = urls[0]
            for u in urls[:50]:  # buscar en los primeros 50 para no tardar
                m = re.search(r"jugada-(\d+)", u)
                if m:
                    idx = int(m.group(1))
                    if idx > max_id:
                        max_id = idx
                        best_url = u

            res = requests.get(best_url, headers=headers, timeout=5)
            if res.status_code != 200:
                return False

            from bs4 import BeautifulSoup

            soup = BeautifulSoup(res.text, "html.parser")
            txt = soup.get_text().replace("\n", " ")

            match_bolas = re.search(r"Jugada Ganadora(.*?)(?:Boliyapa|Gandores)", txt)
            match_yapa = re.search(r"Boliyapa(\d{1,2})", txt)

            if not match_bolas or not match_yapa:
                return False

            numeros_raw = re.findall(r"\d{1,2}", match_bolas.group(1))
            numeros = [int(n) for n in numeros_raw if int(n) > 0][:6]
            boliyapa = int(match_yapa.group(1))

            if len(numeros) != 6:
                return False

            numeros.sort()

            meta_match = re.search(
                r"jugada-(\d+)-del-(\d{1,2}-\d{1,2}-\d{4})", best_url
            )
            if meta_match:
                draw_num = int(meta_match.group(1))
                d_parts = meta_match.group(2).split("-")
                draw_date = f"{d_parts[2]}-{d_parts[1].zfill(2)}-{d_parts[0].zfill(2)}"
            else:
                return False

            self.db.insert_draw(
                draw_num,
                draw_date,
                numeros[0],
                numeros[1],
                numeros[2],
                numeros[3],
                numeros[4],
                numeros[5],
                boliyapa,
            )
            logger.info(f"Último sorteo {draw_num} insertado/actualizado exitosamente.")
            return True

        except Exception as e:
            logger.error(f"Error durante el scraping en vivo: {e}")
            return False

    def crawl_full_history(self):
        """
        Descarga el sitemap de un portal de lotería, extrae todos los enlaces históricos
        (ej. ~318 sorteos de los últimos 5 años) y los raspa de manera concurrente.
        """
        import re
        import concurrent.futures

        sitemap_url = "https://www.tinkaresultados.com/sitemap.xml"
        logger.info(f"Descargando sitemap desde {sitemap_url}...")

        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(sitemap_url, headers=headers, timeout=10)
            if r.status_code != 200:
                logger.error("Error descargando el sitemap.")
                return 0

            # Extraer URLs
            urls = re.findall(
                r"<loc>(https://www.tinkaresultados.com/sorteos-historicos/jugada-[^<]+)</loc>",
                r.text,
            )
            logger.info(f"Se encontraron {len(urls)} sorteos históricos en el sitemap.")

            if not urls:
                return 0

            def fetch_draw(url):
                try:
                    res = requests.get(url, headers=headers, timeout=5)
                    if res.status_code != 200:
                        return None

                    soup = BeautifulSoup(res.text, "html.parser")
                    txt = soup.get_text().replace("\n", " ")

                    # Extraer Bolillas
                    match_bolas = re.search(
                        r"Jugada Ganadora(.*?)(?:Boliyapa|Gandores)", txt
                    )
                    match_yapa = re.search(r"Boliyapa(\d{1,2})", txt)

                    if not match_bolas or not match_yapa:
                        return None

                    numeros_raw = re.findall(r"\d{1,2}", match_bolas.group(1))
                    numeros = [int(n) for n in numeros_raw if int(n) > 0][:6]
                    boliyapa = int(match_yapa.group(1))

                    if len(numeros) != 6:
                        return None

                    numeros.sort()

                    # Extraer Fecha y Numero de la URL (ej: jugada-759-del-14-03-2021)
                    meta_match = re.search(
                        r"jugada-(\d+)-del-(\d{1,2}-\d{1,2}-\d{4})", url
                    )
                    if meta_match:
                        draw_num = int(meta_match.group(1))
                        # format date to YYYY-MM-DD
                        d_parts = meta_match.group(2).split("-")
                        draw_date = (
                            f"{d_parts[2]}-{d_parts[1].zfill(2)}-{d_parts[0].zfill(2)}"
                        )
                    else:
                        return None

                    return {
                        "draw_number": draw_num,
                        "draw_date": draw_date,
                        "b1": numeros[0],
                        "b2": numeros[1],
                        "b3": numeros[2],
                        "b4": numeros[3],
                        "b5": numeros[4],
                        "b6": numeros[5],
                        "boliyapa": boliyapa,
                    }
                except Exception:
                    return None

            valid_draws = []
            # Concurrencia masiva (max 20 hilos)
            logger.info("Iniciando extracción concurrente multihilo...")
            with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
                results = list(executor.map(fetch_draw, urls))

            valid_draws = [d for d in results if d is not None]

            # Ordenar por draw_number para insertar limpiamente
            valid_draws.sort(key=lambda x: x["draw_number"])

            if len(valid_draws) > 0:
                # Limpiar tabla actual directamente usando sqlite3 solo si tenemos nueva data
                import sqlite3

                conn = sqlite3.connect(self.db.db_path)
                conn.execute("DELETE FROM draws")
                conn.commit()
                conn.close()

                inserted = self.db.insert_draws_bulk(valid_draws)
                logger.info(
                    f"Crawling masivo finalizado. {inserted} sorteos reales guardados."
                )
                return inserted
            else:
                logger.warning(
                    "No se extrajeron sorteos válidos. Conservando la base de datos actual."
                )
                return 0

        except Exception as e:
            logger.error(f"Fallo crítico en el Web Crawler: {e}")
            return 0

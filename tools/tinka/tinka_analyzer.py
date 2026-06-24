from collections import Counter
import itertools


class TinkaAnalyzer:
    def __init__(self, db_manager):
        self.db = db_manager

    def get_number_frequencies(self):
        """
        Calcula la frecuencia histórica de cada número (bolillas 1 a 6)
        excluyendo la boliyapa.
        Retorna un diccionario {numero: frecuencia} ordenado de mayor a menor.
        """
        draws = self.db.get_all_draws()
        all_numbers = []

        for draw in draws:
            all_numbers.extend(
                [draw["b1"], draw["b2"], draw["b3"], draw["b4"], draw["b5"], draw["b6"]]
            )

        counter = Counter(all_numbers)
        # Ordenar por frecuencia descendente
        sorted_freq = dict(
            sorted(counter.items(), key=lambda item: item[1], reverse=True)
        )
        return sorted_freq

    def get_droughts(self, current_draw_num):
        """
        Calcula hace cuántos sorteos no sale cada número.
        """
        draws = self.db.get_all_draws()
        # Encontrar el máximo dinámicamente
        max_num = max(
            [
                n
                for draw in draws
                for n in (
                    draw["b1"],
                    draw["b2"],
                    draw["b3"],
                    draw["b4"],
                    draw["b5"],
                    draw["b6"],
                )
            ]
            + [50]
        )
        # Inicializar todos en el máximo posible o en 'No ha salido'
        last_seen = {i: None for i in range(1, max_num + 1)}

        for draw in draws:
            draw_num = draw["draw_number"]
            numbers = [
                draw["b1"],
                draw["b2"],
                draw["b3"],
                draw["b4"],
                draw["b5"],
                draw["b6"],
            ]
            for n in numbers:
                # Como recorremos del más antiguo al más nuevo (o viceversa),
                # siempre actualizamos con el último sorteo donde apareció
                if last_seen.get(n) is None or draw_num > last_seen[n]:
                    last_seen[n] = draw_num

        droughts = {}
        for num, last_draw in last_seen.items():
            if last_draw is None:
                droughts[num] = float("inf")  # Nunca ha salido
            else:
                droughts[num] = current_draw_num - last_draw

        # Ordenar de mayor sequía a menor
        return dict(sorted(droughts.items(), key=lambda item: item[1], reverse=True))

    def get_common_pairs(self, top_n=20):
        """
        Encuentra los pares de números que más veces han salido juntos en un mismo sorteo.
        """
        draws = self.db.get_all_draws()
        pair_counter = Counter()

        for draw in draws:
            numbers = [
                draw["b1"],
                draw["b2"],
                draw["b3"],
                draw["b4"],
                draw["b5"],
                draw["b6"],
            ]
            numbers.sort()
            # Combinaciones posibles de 2 dentro de las 6 bolillas
            pairs = itertools.combinations(numbers, 2)
            pair_counter.update(pairs)

        return pair_counter.most_common(top_n)

    def get_even_odd_distribution(self):
        """
        Calcula la distribución histórica de Pares vs Impares por sorteo.
        (ej. 3 pares y 3 impares es lo más común).
        """
        draws = self.db.get_all_draws()
        distribution = Counter()

        for draw in draws:
            numbers = [
                draw["b1"],
                draw["b2"],
                draw["b3"],
                draw["b4"],
                draw["b5"],
                draw["b6"],
            ]
            evens = sum(1 for n in numbers if n % 2 == 0)
            odds = 6 - evens
            dist_key = f"{evens}P-{odds}I"
            distribution[dist_key] += 1

        return dict(
            sorted(distribution.items(), key=lambda item: item[1], reverse=True)
        )

    def get_hot_and_cold_numbers(self, window_size=50):
        """
        Obtiene los números 'calientes' (más frecuentes en los últimos N sorteos)
        y los 'fríos' (menos frecuentes en los últimos N sorteos).
        """
        draws = self.db.get_all_draws()
        # Tomar solo los últimos window_size sorteos
        recent_draws = draws[-window_size:] if len(draws) > window_size else draws

        all_numbers = []
        for draw in recent_draws:
            all_numbers.extend(
                [draw["b1"], draw["b2"], draw["b3"], draw["b4"], draw["b5"], draw["b6"]]
            )

        counter = Counter(all_numbers)
        max_num = max(all_numbers + [50]) if all_numbers else 50
        # Hay números que podrían no haber salido en la ventana, su frecuencia es 0
        for i in range(1, max_num + 1):
            if i not in counter:
                counter[i] = 0

        sorted_freq = sorted(counter.items(), key=lambda item: item[1])

        cold_numbers = sorted_freq[:10]
        hot_numbers = sorted_freq[-10:]
        hot_numbers.reverse()  # Mayor a menor

        return {"hot": dict(hot_numbers), "cold": dict(cold_numbers)}

    def get_markov_transitions(self, top_n=5):
        """
        Calcula una Cadena de Markov (Matriz de Transición de Probabilidades).
        Evalúa, si el número X salió en el sorteo T, ¿cuáles son los números más probables
        que saldrán en el sorteo T+1?
        Retorna las transiciones más fuertes de los números del último sorteo.
        """
        draws = self.db.get_all_draws()
        if len(draws) < 2:
            return {}

        from collections import defaultdict

        transitions = defaultdict(Counter)

        # Construir matriz de ocurrencias subsecuentes
        for i in range(len(draws) - 1):
            current_draw = draws[i]
            next_draw = draws[i + 1]

            curr_nums = [
                current_draw["b1"],
                current_draw["b2"],
                current_draw["b3"],
                current_draw["b4"],
                current_draw["b5"],
                current_draw["b6"],
            ]
            next_nums = [
                next_draw["b1"],
                next_draw["b2"],
                next_draw["b3"],
                next_draw["b4"],
                next_draw["b5"],
                next_draw["b6"],
            ]

            for num in curr_nums:
                for nxt_num in next_nums:
                    transitions[num][nxt_num] += 1

        # Obtener los números del ÚLTIMO sorteo para predecir el futuro
        latest_draw = draws[-1]
        latest_nums = [
            latest_draw["b1"],
            latest_draw["b2"],
            latest_draw["b3"],
            latest_draw["b4"],
            latest_draw["b5"],
            latest_draw["b6"],
        ]

        markov_peaks = {}
        for num in latest_nums:
            # Los top_n números que más suelen seguir a 'num'
            top_transitions = transitions[num].most_common(top_n)
            total_transitions = sum(transitions[num].values())

            prob_list = []
            for nxt, count in top_transitions:
                prob = (
                    round((count / total_transitions) * 100, 2)
                    if total_transitions > 0
                    else 0
                )
                prob_list.append(f"{nxt} ({prob}%)")

            markov_peaks[num] = prob_list

        return markov_peaks

import sqlite3
import os
from datetime import datetime

class TinkaDB:
    def __init__(self, db_path="tinka_history.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Inicializa la base de datos y crea la tabla si no existe."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS draws (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            draw_number INTEGER UNIQUE NOT NULL,
            draw_date TEXT NOT NULL,
            b1 INTEGER NOT NULL,
            b2 INTEGER NOT NULL,
            b3 INTEGER NOT NULL,
            b4 INTEGER NOT NULL,
            b5 INTEGER NOT NULL,
            b6 INTEGER NOT NULL,
            boliyapa INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        conn.close()

    def insert_draw(self, draw_number, draw_date, b1, b2, b3, b4, b5, b6, boliyapa=None):
        """Inserta o actualiza un sorteo en la base de datos."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            INSERT INTO draws (draw_number, draw_date, b1, b2, b3, b4, b5, b6, boliyapa)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(draw_number) DO UPDATE SET
                draw_date=excluded.draw_date,
                b1=excluded.b1,
                b2=excluded.b2,
                b3=excluded.b3,
                b4=excluded.b4,
                b5=excluded.b5,
                b6=excluded.b6,
                boliyapa=excluded.boliyapa
            ''', (draw_number, draw_date, b1, b2, b3, b4, b5, b6, boliyapa))
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error al insertar sorteo {draw_number}: {e}")
            return False
        finally:
            conn.close()

    def insert_draws_bulk(self, draws_list):
        """
        Inserta múltiples sorteos a la vez.
        draws_list debe ser una lista de diccionarios con las claves correspondientes.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        inserted_count = 0
        try:
            for draw in draws_list:
                cursor.execute('''
                INSERT INTO draws (draw_number, draw_date, b1, b2, b3, b4, b5, b6, boliyapa)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(draw_number) DO NOTHING
                ''', (
                    draw.get('draw_number'), 
                    draw.get('draw_date'),
                    draw.get('b1'), draw.get('b2'), draw.get('b3'),
                    draw.get('b4'), draw.get('b5'), draw.get('b6'),
                    draw.get('boliyapa')
                ))
                if cursor.rowcount > 0:
                    inserted_count += 1
            conn.commit()
            return inserted_count
        except sqlite3.Error as e:
            print(f"Error en inserción masiva: {e}")
            return -1
        finally:
            conn.close()

    def get_all_draws(self):
        """Obtiene todos los sorteos ordenados por número de sorteo (ascendente)."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM draws ORDER BY draw_number ASC')
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]

    def get_latest_draw(self):
        """Obtiene el último sorteo registrado."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM draws ORDER BY draw_number DESC LIMIT 1')
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None

    def get_total_draws_count(self):
        """Retorna la cantidad total de sorteos registrados."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM draws')
        count = cursor.fetchone()[0]
        conn.close()
        
        return count

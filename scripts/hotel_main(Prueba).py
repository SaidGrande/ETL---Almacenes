import pandas as pd
import json
import psycopg2
from datetime import datetime

class HotelDataProcessor:
    def __init__(self):
        self.data = None

    def load_data(self, file_path: str):
        """Carga datos desde CSV, Excel o JSON."""
        try:
            if file_path.endswith('.csv'):
                self.data = pd.read_csv(file_path)
            elif file_path.endswith('.xlsx'):
                self.data = pd.read_excel(file_path)
            elif file_path.endswith('.json'):
                with open(file_path, 'r') as f:
                    self.data = pd.json_normalize(json.load(f))
            print("Datos cargados correctamente.")
        except Exception as e:
            print(f"Error al cargar {file_path}: {e}")

    def clean_data(self):
        """Limpieza y transformaciones."""
        # 1. Corregir fechas (ej: columnas separadas a una sola)
        self.data['arrival_date'] = pd.to_datetime(
            self.data['arrival_date_year'].astype(str) + '-' +
            self.data['arrival_date_month'] + '-' +
            self.data['arrival_date_day_of_month'].astype(str),
            errors='coerce'  # Ignora formatos inválidos
        )

        # 2. Rellenar valores nulos
        self.data['children'].fillna(0, inplace=True)
        self.data['country'].fillna('Unknown', inplace=True)

        # 3. Nueva columna: Clasificación por tarifa
        self.data['price_category'] = pd.cut(
            self.data['adr'],
            bins=[0, 100, 200, float('inf')],
            labels=['Económico', 'Estándar', 'Premium']
        )

    def save_data(self, output_type: str, db_config=None):
        """Guarda los datos procesados."""
        try:
            if output_type == 'csv':
                self.data.to_csv('cleaned_hotel_data.csv', index=False)
            elif output_type == 'excel':
                self.data.to_excel('cleaned_hotel_data.xlsx', index=False)
            elif output_type == 'json':
                self.data.to_json('cleaned_hotel_data.json', orient='records')
            elif output_type == 'postgresql':
                conn = psycopg2.connect(**db_config)
                self.data.to_sql('hotel_bookings', conn, if_exists='replace', index=False)
                conn.close()
            print(f"Datos guardados como {output_type}.")
        except Exception as e:
            print(f"Error al guardar: {e}")

def main():
    processor = HotelDataProcessor()
    
    # 1. Cargar datos
    file_path = input("C:\\Users\\Wakeful\\Desktop\\ETL - Almacenes\\Data\\hotel_bookings.csv")
    processor.load_data(file_path)

    # 2. Limpiar datos
    processor.clean_data()

    # 3. Guardar resultados
    output_type = input("¿Guardar como? (csv/excel/json/postgresql): ").lower()
    if output_type == 'postgresql':
        db_config = {
            'host': 'localhost',
            'database': 'hotel_db',
            'user': 'postgres',
            'password': 'Admin'
        }
        processor.save_data(output_type, db_config)
    else:
        processor.save_data(output_type)

if __name__ == "__main__":
    main()
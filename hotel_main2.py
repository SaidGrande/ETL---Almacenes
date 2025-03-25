import pandas as pd
import json
import psycopg2
from psycopg2 import OperationalError
import os
from abc import ABC, abstractmethod
import sys
from datetime import datetime

class DataLoader(ABC):
    """Clase abstracta para cargar datos desde diferentes fuentes"""
    @abstractmethod
    def load_data(self):
        pass

class CSVDataLoader(DataLoader):
    """Cargador de datos desde archivos CSV"""
    def __init__(self, file_path):
        self.file_path = file_path

    def load_data(self):
        try:
            return pd.read_csv(self.file_path)
        except FileNotFoundError:
            print(f"Error: No se encontró el archivo {self.file_path}")
            return None
        except Exception as e:
            print(f"Error al cargar CSV: {str(e)}")
            return None

class ExcelDataLoader(DataLoader):
    """Cargador de datos desde archivos Excel"""
    def __init__(self, file_path):
        self.file_path = file_path

    def load_data(self):
        try:
            return pd.read_excel(self.file_path)
        except FileNotFoundError:
            print(f"Error: No se encontró el archivo {self.file_path}")
            return None
        except Exception as e:
            print(f"Error al cargar Excel: {str(e)}")
            return None

class JSONDataLoader(DataLoader):
    """Cargador de datos desde archivos JSON"""
    def __init__(self, file_path):
        self.file_path = file_path

    def load_data(self):
        try:
            with open(self.file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            return pd.DataFrame(data)
        except FileNotFoundError:
            print(f"Error: No se encontró el archivo {self.file_path}")
            return None
        except Exception as e:
            print(f"Error al cargar JSON: {str(e)}")
            return None

class PostgreSQLDataLoader(DataLoader):
    """Cargador de datos desde PostgreSQL"""
    def __init__(self, dbname, user, password, host, port, table_name):
        self.dbname = dbname
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.table_name = table_name

    def load_data(self):
        try:
            connection = psycopg2.connect(
                dbname=self.dbname,
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port
            )
            query = f"SELECT * FROM {self.table_name}"
            return pd.read_sql(query, connection)
        except OperationalError as e:
            print(f"Error de conexión a PostgreSQL: {str(e)}")
            return None
        except Exception as e:
            print(f"Error al cargar desde PostgreSQL: {str(e)}")
            return None



class DataCleaner:
    """Clase para limpieza y transformación de datos"""
    def __init__(self, data):
        self.data = data

    def clean_data(self):
        """Realiza todas las operaciones de limpieza"""
        if self.data is None:
            return None

        try:
            # Convertir fechas a formato estándar
            self._convert_dates()

            # Manejar valores nulos
            self._handle_nulls()

            # Crear nuevas columnas
            self._create_new_columns()

            # Estandarizar formatos
            self._standardize_formats()

            return self.data
        except Exception as e:
            print(f"Error durante la limpieza: {str(e)}")
            return None

    def _convert_dates(self):
        """Convertir todas las columnas de fecha a formato estándar"""
        date_columns = ['reservation_status_date', 'arrival_date']

        for col in date_columns:
            if col in self.data.columns:
                try:
                        # Intentar varios formatos de fecha comunes
                        self.data[col] = pd.to_datetime(
                        self.data[col],
                        errors='coerce',
                        format='mixed',
                        dayfirst=True
                    )
                except:
                    # Si falla, simplemente mantener como está
                    pass

    def _handle_nulls(self):
        """Manejar valores nulos según el tipo de columna"""
        for col in self.data.columns:
            if self.data[col].isnull().any():
                if self.data[col].dtype == 'object':
                    # Para columnas categóricas, usar 'Desconocido'
                    self.data[col].fillna('Desconocido', inplace=True)
                else:
                    # Para numéricas, usar la mediana
                    self.data[col].fillna(self.data[col].median(), inplace=True)

    def _create_new_columns(self):
        """Crear nuevas columnas derivadas"""
        # Duración de la estancia
        if 'arrival_date' in self.data.columns and 'departure_date' in self.data.columns:
            self.data['stay_duration'] = (self.data['departure_date'] - self.data['arrival_date']).dt.days

        # Total de personas (adultos + niños + bebés)
        person_columns = ['adults', 'children', 'babies']
        if all(col in self.data.columns for col in person_columns):
            self.data['total_guests'] = self.data[person_columns].sum(axis=1)

        # Temporada (alta/media/baja) basada en el mes de llegada
        if 'arrival_date_month' in self.data.columns:
            seasons = {
                'January': 'Baja', 'February': 'Baja', 'March': 'Media',
                'April': 'Media', 'May': 'Media', 'June': 'Alta',
                'July': 'Alta', 'August': 'Alta', 'September': 'Media',
                'October': 'Media', 'November': 'Media', 'December': 'Alta'
            }
            self.data['season'] = self.data['arrival_date_month'].map(seasons)

    def _standardize_formats(self):
        """Estandarizar formatos de texto"""
        if 'country' in self.data.columns:
            self.data['country'] = self.data['country'].str.upper()

        if 'customer_type' in self.data.columns:
            self.data['customer_type'] = self.data['customer_type'].str.capitalize()



# Ruta donde se guardan los nuevos archivos (asegúrate de que esta ruta existe)
salidan = 'C:\\Users\\Wakeful\\Desktop\\ETL - Almacenes\\output\\'

class DataSaver:
    """Clase para guardar datos en diferentes formatos"""
    @staticmethod
    def save_data(data, save_option, file_path=None, db_config=None):
        """Guarda los datos según la opción seleccionada"""
        if data is None:
            print("No hay datos para guardar.")
            return False

        try:
            # Asegurar que el directorio existe
            os.makedirs(salidan, exist_ok=True)

            if save_option == '1':  # CSV
                if not file_path:
                    file_path = os.path.join(salidan, 'hotel_bookings_clean.csv')
                else:
                    # Si el usuario proporciona ruta pero no incluye el directorio
                    if not os.path.dirname(file_path):
                        file_path = os.path.join(salidan, file_path)
                data.to_csv(file_path, index=False)
                print(f"Datos guardados exitosamente en {file_path}")
                return True

            elif save_option == '2':  # Excel
                if not file_path:
                    file_path = os.path.join(salidan, 'hotel_bookings_clean.xlsx')
                else:
                    if not os.path.dirname(file_path):
                        file_path = os.path.join(salidan, file_path)
                data.to_excel(file_path, index=False)
                print(f"Datos guardados exitosamente en {file_path}")
                return True

            elif save_option == '3':  # JSON
                if not file_path:
                    file_path = os.path.join(salidan, 'hotel_bookings_clean.json')
                else:
                    if not os.path.dirname(file_path):
                        file_path = os.path.join(salidan, file_path)
                data.to_json(file_path, orient='records', indent=4)
                print(f"Datos guardados exitosamente en {file_path}")
                return True

            elif save_option == '4':  # PostgreSQL
                if not db_config:
                    print("Se requieren parámetros de conexión a la base de datos.")
                    return False

                try:
                    connection = psycopg2.connect(**db_config)
                    data.to_sql('hotel_bookings_clean', connection, if_exists='replace', index=False)
                    print("Datos guardados exitosamente en PostgreSQL")
                    return True
                except Exception as db_error:
                    print(f"Error al guardar en PostgreSQL: {str(db_error)}")
                    return False

            else:
                print("Opcion no valida.")
                return False
        except Exception as e:
            print(f"Error al guardar datos: {str(e)}")
            return False



class HotelBookingAnalysis:
    """Clase principal del sistema de análisis"""
    def __init__(self):
        self.data = None
        self.clean_data = None




        # Rutas precargadas por defecto
        self.default_paths = {
            'csv': 'C:\\Users\\Wakeful\\Desktop\\ETL - Almacenes\\Data\\hotel_bookings.csv',
            'excel': 'C:\\Users\\Wakeful\\Desktop\\ETL - Almacenes\\Data\\hotel_bookings.xlsx',
            'json': 'C:\\Users\\Wakeful\\Desktop\\ETL - Almacenes\\Data\\hotel_bookings.json'
        }





    def run(self):
        """Método principal para ejecutar el sistema"""
        print("\n=== Sistema de Análisis de Reservaciones Hoteleras ===")

        # Primero intenta carga automática
        if not self._load_data_auto():
            # Si falla, usa el método interactivo
            self._load_data_interactive()

        if self.data is None:
            print("No se pudo cargar ningún conjunto de datos. Saliendo...")
            return

        # Limpiar y transformar datos
        print("\nRealizando limpieza y transformación de datos...")
        cleaner = DataCleaner(self.data)
        self.clean_data = cleaner.clean_data()

        if self.clean_data is None:
            print("Error durante la limpieza de datos. Saliendo...")
            return

        # Mostrar resumen de datos limpios
        print("\nResumen de datos limpios:")
        print(self.clean_data.info())
        print("\nPrimeras filas de datos limpios:")
        print(self.clean_data.head())

        # Guardar datos
        self._save_data()

    def _load_data_auto(self):
        """Intenta cargar automáticamente de las rutas precargadas"""
        print("\nIntentando carga automática desde rutas precargadas...")

        # Orden de intentos de carga
        formats_to_try = ['csv', 'excel', 'json']

        for file_format in formats_to_try:
            file_path = self.default_paths[file_format]
            print(f"\nIntentando cargar {file_path}...")

            if file_format == 'csv':
                loader = CSVDataLoader(file_path)
            elif file_format == 'excel':
                loader = ExcelDataLoader(file_path)
            elif file_format == 'json':
                loader = JSONDataLoader(file_path)

            self.data = loader.load_data()

            if self.data is not None:
                print(f"¡Éxito! Datos cargados desde {file_path}")
                return True

        print("\nNo se pudo cargar ningún archivo automáticamente.")
        return False

    def _load_data_interactive(self):
        """Interfaz interactiva para cargar datos"""
        print("\nOpciones para cargar datos:")
        print("1. Desde archivo CSV")
        print("2. Desde archivo Excel")
        print("3. Desde archivo JSON")
        print("4. Desde PostgreSQL - Prueba aun no charcha")
        print("5. Salir")

        option = input("\nSeleccione una opción (1-5): ")

        if option == '1':
            file_path = input(f"Ingrese la ruta del archivo CSV (dejar en blanco para '{self.default_paths['csv']}'): ")
            file_path = file_path if file_path else self.default_paths['csv']
            loader = CSVDataLoader(file_path)
            self.data = loader.load_data()

        elif option == '2':
            file_path = input(f"Ingrese la ruta del archivo Excel (dejar en blanco para '{self.default_paths['excel']}'): ")
            file_path = file_path if file_path else self.default_paths['excel']
            loader = ExcelDataLoader(file_path)
            self.data = loader.load_data()

        elif option == '3':
            file_path = input(f"Ingrese la ruta del archivo JSON (dejar en blanco para '{self.default_paths['json']}'): ")
            file_path = file_path if file_path else self.default_paths['json']
            loader = JSONDataLoader(file_path)
            self.data = loader.load_data()

        elif option == '4':
            print("\nIngrese los parámetros de conexión a PostgreSQL:")
            dbname = input("Nombre de la base de datos: ")
            user = input("Usuario: ")
            password = input("Contraseña: ")
            host = input("Host (dejar en blanco para localhost): ") or "localhost"
            port = input("Puerto (dejar en blanco para 5432): ") or "5432"
            table_name = input("Nombre de la tabla: ")

            loader = PostgreSQLDataLoader(dbname, user, password, host, port, table_name)
            self.data = loader.load_data()

        elif option == '5':
            print("Saliendo...")
            sys.exit()

        else:
            print("Opción no válida. Intente nuevamente.")
            self._load_data_interactive()

    def _save_data(self):
        """Interfaz para guardar datos en diferentes formatos"""
        print("\nOpciones para guardar datos limpios:")
        print("1. Guardar como CSV")
        print("2. Guardar como Excel")
        print("3. Guardar como JSON")
        print("4. Guardar en PostgreSQL - (Prueba xD - aun no jala uwu)")
        print("5. No guardar y salir")

        option = input("\nSeleccione una opción (1-5): ")

        if option in ['1', '2', '3']:
            default_name = f"hotel_bookings_clean.{'csv' if option == '1' else 'xlsx' if option == '2' else 'json'}"
            custom_path = input(f"Ingrese SOLO el nombre del archivo (dejar en blanco para '{default_name}'): ")
            
            if custom_path:
                file_path = os.path.join(salidan, custom_path)
            else:
                file_path = os.path.join(salidan, default_name)
                
            success = DataSaver.save_data(self.clean_data, option, file_path)

            if not success:
                print("¿Desea intentar con otra opción? (s/n)")
                retry = input().lower()
                if retry == 's':
                    self._save_data()

        elif option == '4':
            print("\nIngrese los parámetros de conexión a PostgreSQL:")
            db_config = {
                'dbname': input("Nombre de la base de datos: "),
                'user': input("Usuario: "),
                'password': input("Contraseña: "),
                'host': input("Host (dejar en blanco para localhost): ") or "localhost",
                'port': input("Puerto (dejar en blanco para 5432): ") or "5432"
            }

            success = DataSaver.save_data(self.clean_data, option, db_config=db_config)

            if not success:
                print("¿Desea intentar con otra opción? (s/n)")
                retry = input().lower()
                if retry == 's':
                    self._save_data()

        elif option == '5':
            print("Saliendo sin guardar...")
        else:
            print("Opción no válida. Intente nuevamente.")
            self._save_data()

#MAIN
if __name__ == "__main__":
    try:
        analysis_system = HotelBookingAnalysis()
        analysis_system.run()
    except KeyboardInterrupt:
        print("\nOperación cancelada por el usuario.")
    except Exception as e:
        print(f"Error inesperado: {str(e)}")
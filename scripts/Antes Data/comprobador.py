import pandas as pd
import sys

try:
    df_excel = pd.read_excel('C:\\Users\\Wakeful\\Desktop\\ETL - Almacenes\\Data\\hotel_bookings.xlsx')
    df_json = pd.read_json('C:\\Users\\Wakeful\\Desktop\\ETL - Almacenes\\Data\\hotel_bookings.json')
    
    print("Excel - Columnas:", df_excel.columns.tolist())
    print("JSON - Primer registro:", df_json.iloc[0].to_dict())

    print("\n Comprobando...")
    
    df_csv = pd.read_csv('C:\\Users\\Wakeful\\Desktop\\ETL - Almacenes\\Data\\hotel_bookings.csv')
    if df_csv.shape == df_excel.shape:
        print("\n\n")
        print("Excel y CSV tienen las mismas dimensiones.")
    else:
        print("Error: Tamaños no coinciden.")
        
except Exception as e:
    print(f"Error al verificar: {e}")
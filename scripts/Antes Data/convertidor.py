import pandas as pd

# Cargar el archivo CSV
df = pd.read_csv('C:\\Users\\Wakeful\\Desktop\\ETL - Almacenes\\Data\\hotel_bookings.csv')

#Ruta donde se guardan los nuevos archivos
salida = 'C:\\Users\\Wakeful\\Desktop\\ETL - Almacenes\\Data\\'

# Convertir a Excel (requiere openpyxl)
df.to_excel(salida + 'hotel_bookings.xlsx', index=False, engine='openpyxl')  

# Convertir a JSON
df.to_json(salida +'hotel_bookings.json', orient='records')

print(" Conversion completada: CSV -> Excel y JSON")
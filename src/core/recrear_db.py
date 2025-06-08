import sqlite3
import os

# Ruta de la carpeta y archivo de base de datos
db_path = os.path.join("src/database", "system_monitor.db")

# Crear la carpeta si no existe
if not os.path.exists(folder):
    os.makedirs(folder)
    print(f"📁 Carpeta '{folder}' creada.")

# Eliminar base de datos anterior si existe
if os.path.exists(db_path):
    os.remove(db_path)
    print("🗑️ Archivo 'system_monitor.db' anterior eliminado.")

# Crear nueva base de datos
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Crear tabla 'alerts' con columna 'severity'
cursor.execute("""
CREATE TABLE alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message TEXT,
    timestamp TEXT,
    severity TEXT
)
""")

conn.commit()
conn.close()

print("✅ Base de datos 'system_monitor.db' creada correctamente con la tabla 'alerts'.")

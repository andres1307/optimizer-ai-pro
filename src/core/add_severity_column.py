import sqlite3

# Ruta al archivo de base de datos SQLite
db_path = "src/database/system_monitor.db"  # Asegúrate que esta ruta es correcta desde donde ejecutas este script

# Conectar a la base de datos
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Verificar si la columna 'severity' ya existe
cursor.execute("PRAGMA table_info(alerts)")
columns = cursor.fetchall()
column_names = [col[1] for col in columns]

# Si no existe la columna, la agregamos
if 'severity' not in column_names:
    try:
        cursor.execute("ALTER TABLE alerts ADD COLUMN severity TEXT")
        conn.commit()
        print("✅ Columna 'severity' agregada correctamente a la tabla 'alerts'.")
    except sqlite3.OperationalError as e:
        print(f"⚠️ Error al intentar agregar la columna: {e}")
else:
    print("ℹ️ La columna 'severity' ya existe en la tabla 'alerts'.")

# Cerrar la conexión
conn.close()

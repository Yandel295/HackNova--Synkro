import sqlite3
import os

# Nombre de la base de datos
DB_NAME = "database.db"

# Crear carpeta si no existe
if not os.path.exists('uploads'):
    os.makedirs('uploads')

# Conectar a SQLite
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

# -------------------------------
# Crear tabla folders
# -------------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS folders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
)
""")

# -------------------------------
# Crear tabla pdfs
# -------------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS pdfs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    folder_id INTEGER NOT NULL,
    FOREIGN KEY (folder_id) REFERENCES folders(id) ON DELETE CASCADE
)
""")

conn.commit()
conn.close()
print("Base de datos creada correctamente con tablas 'folders' y 'pdfs'.")

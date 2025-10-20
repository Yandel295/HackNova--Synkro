import sqlite3
import os

# Nombre del archivo de la base de datos
DB_NAME = "dataBase.db"

# Si ya existe la DB, opcionalmente la borramos para empezar de cero
if os.path.exists(DB_NAME):
    os.remove(DB_NAME)
    print(f"Se eliminó la base de datos anterior '{DB_NAME}'.")

# Conectamos a la base de datos (se crea si no existe)
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

# Creamos la tabla de carpetas
cursor.execute("""
CREATE TABLE folders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);
""")
print("Tabla 'folders' creada correctamente.")

# Creamos la tabla de PDFs
cursor.execute("""
CREATE TABLE pdfs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    folder_id INTEGER NOT NULL,
    filename TEXT NOT NULL,
    tags TEXT,
    FOREIGN KEY (folder_id) REFERENCES folders(id) ON DELETE CASCADE
);
""")
print("Tabla 'pdfs' creada correctamente.")

conn.commit()
conn.close()
print("Base de datos inicializada con éxito.")

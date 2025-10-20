import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# Tabla de carpetas
cursor.execute("""
CREATE TABLE IF NOT EXISTS folders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
)
""")

# Tabla de PDFs
cursor.execute("""
CREATE TABLE IF NOT EXISTS pdfs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    folder_id INTEGER,
    filename TEXT NOT NULL,
    tags TEXT,
    upload_date TEXT,
    FOREIGN KEY(folder_id) REFERENCES folders(id)
)
""")

conn.commit()
conn.close()

print("✅ Base de datos creada correctamente con la columna upload_date.")

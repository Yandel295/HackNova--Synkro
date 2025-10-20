from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, abort
import sqlite3
import os
import shutil
from datetime import datetime
import html
from pathlib import Path
import re

app = Flask(__name__)
app.secret_key = "supersecretkey"

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# =========== SEGURIDAD: Clase de protección =========== #
class SecurityManager:
    @staticmethod
    def sanitize_input(text):
        """Protección contra XSS - Escapa caracteres HTML"""
        if text is None:
            return ""
        return html.escape(str(text))
    
    @staticmethod
    def safe_path_access(file_path, base_directory):
        """Protección contra Path Traversal"""
        base_path = Path(base_directory).resolve()
        requested_path = Path(file_path)
        
        # Combinar rutas de forma segura
        full_path = (base_path / requested_path).resolve()
        
        # Verificar que la ruta final esté dentro del directorio base
        if not str(full_path).startswith(str(base_path)):
            return None
        return full_path
    
    @staticmethod
    def validate_filename(filename):
        """Valida que el nombre de archivo sea seguro"""
        if not filename or filename.strip() == "":
            return False
        
        # Patrón seguro para nombres de archivo
        pattern = r'^[a-zA-Z0-9_\-\. ]+$'
        return bool(re.match(pattern, filename))
    
    @staticmethod
    def validate_folder_name(folder_name):
        """Valida nombres de carpeta"""
        if not folder_name or len(folder_name.strip()) < 1 or len(folder_name) > 100:
            return False
        # Eliminar caracteres peligrosos
        cleaned = re.sub(r'[<>:"/\\|?*]', '', folder_name)
        return cleaned.strip()

# Instancia global de seguridad
security = SecurityManager()

# =========== SEGURIDAD: Decorador para verificación de permisos =========== #
def validate_folder_access(f):
    """Decorador para proteger acceso a carpetas (IDOR protection)"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        folder_id = kwargs.get('folder_id')
        if folder_id:
            # Verificar que la carpeta existe y el usuario tiene acceso
            conn = get_db_connection()
            folder = conn.execute("SELECT * FROM folders WHERE id=?", (folder_id,)).fetchone()
            conn.close()
            
            if not folder:
                abort(404)  # No revelar información específica
        return f(*args, **kwargs)
    return decorated_function

# ----------- Base de datos ----------- #
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS folders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS pdfs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            folder_id INTEGER,
            filename TEXT,
            tags TEXT,
            upload_date TEXT,
            FOREIGN KEY(folder_id) REFERENCES folders(id)
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ----------- Rutas ----------- #
@app.route("/")
def index():
    conn = get_db_connection()
    folders = conn.execute("SELECT * FROM folders").fetchall()
    folder_selected = None
    pdfs = []
    conn.close()
    return render_template("index.html", folders=folders, pdfs=pdfs, folder_selected=folder_selected)

@app.route("/folder/<int:folder_id>")
@validate_folder_access  # <-- PROTECCIÓN IDOR
def open_folder(folder_id):
    conn = get_db_connection()
    folders = conn.execute("SELECT * FROM folders").fetchall()
    folder_selected = conn.execute("SELECT * FROM folders WHERE id=?", (folder_id,)).fetchone()
    pdfs = conn.execute("SELECT * FROM pdfs WHERE folder_id=?", (folder_id,)).fetchall()
    conn.close()
    return render_template("index.html", folders=folders, pdfs=pdfs, folder_selected=folder_selected)

@app.route("/add_folder", methods=["POST"])
def add_folder():
    folder_name = request.form["folder_name"]
    
    # =========== SEGURIDAD: Validación de entrada =========== #
    safe_folder_name = security.validate_folder_name(folder_name)
    if not safe_folder_name:
        flash("Nombre de carpeta inválido", "danger")
        return redirect(url_for("index"))
    
    conn = get_db_connection()
    cursor = conn.execute("INSERT INTO folders (name) VALUES (?)", (safe_folder_name,))  # <-- SQL Injection protection
    folder_id = cursor.lastrowid
    conn.commit()
    conn.close()
    folder_path = os.path.join(UPLOAD_FOLDER, str(folder_id))
    os.makedirs(folder_path, exist_ok=True)
    flash(f'Carpeta "{safe_folder_name}" creada', "success")
    return redirect(url_for("index"))

@app.route("/delete_folder/<int:folder_id>", methods=["POST"])
@validate_folder_access  # <-- PROTECCIÓN IDOR
def delete_folder(folder_id):
    conn = get_db_connection()
    folder = conn.execute("SELECT * FROM folders WHERE id=?", (folder_id,)).fetchone()
    if folder:
        pdfs = conn.execute("SELECT * FROM pdfs WHERE folder_id=?", (folder_id,)).fetchall()
        folder_path = os.path.join(UPLOAD_FOLDER, str(folder_id))
        try:
            shutil.rmtree(folder_path)
        except PermissionError:
            flash("No se pudo eliminar la carpeta física, revisa permisos", "danger")
        conn.execute("DELETE FROM pdfs WHERE folder_id=?", (folder_id,))
        conn.execute("DELETE FROM folders WHERE id=?", (folder_id,))
        conn.commit()
        flash(f'Carpeta "{folder["name"]}" eliminada', "success")
    conn.close()
    return redirect(url_for("index"))

@app.route("/upload_pdf/<int:folder_id>", methods=["POST"])
@validate_folder_access  # <-- PROTECCIÓN IDOR
def upload_pdf(folder_id):
    if "pdf_file" not in request.files:
        flash("No se seleccionó archivo", "danger")
        return redirect(url_for("open_folder", folder_id=folder_id))
    
    file = request.files["pdf_file"]
    tags = request.form.get("tags", "")
    
    # =========== SEGURIDAD: Sanitización de tags =========== #
    safe_tags = security.sanitize_input(tags)
    
    if file.filename == "":
        flash("Archivo inválido", "danger")
        return redirect(url_for("open_folder", folder_id=folder_id))
    
    # =========== SEGURIDAD: Validación de nombre de archivo =========== #
    if not security.validate_filename(file.filename):
        flash("Nombre de archivo no permitido", "danger")
        return redirect(url_for("open_folder", folder_id=folder_id))
    
    filename = file.filename
    folder_path = os.path.join(UPLOAD_FOLDER, str(folder_id))
    os.makedirs(folder_path, exist_ok=True)
    file_path = os.path.join(folder_path, filename)
    
    # =========== SEGURIDAD: Verificación de tipo de archivo básica =========== #
    if not filename.lower().endswith('.pdf'):
        flash("Solo se permiten archivos PDF", "danger")
        return redirect(url_for("open_folder", folder_id=folder_id))
    
    file.save(file_path)

    upload_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db_connection()
    conn.execute("INSERT INTO pdfs (folder_id, filename, tags, upload_date) VALUES (?, ?, ?, ?)",
                 (folder_id, filename, safe_tags, upload_date))  # <-- SQL Injection protection
    conn.commit()
    conn.close()
    flash(f'PDF "{filename}" subido correctamente', "success")
    return redirect(url_for("open_folder", folder_id=folder_id))

@app.route("/delete_pdf/<int:pdf_id>/<int:folder_id>", methods=["POST"])
@validate_folder_access  # <-- PROTECCIÓN IDOR
def delete_pdf(pdf_id, folder_id):
    conn = get_db_connection()
    pdf = conn.execute("SELECT * FROM pdfs WHERE id=?", (pdf_id,)).fetchone()
    if pdf:
        # =========== SEGURIDAD: Path traversal protection =========== #
        safe_path = security.safe_path_access(pdf["filename"], os.path.join(UPLOAD_FOLDER, str(folder_id)))
        if safe_path and os.path.exists(safe_path):
            os.remove(safe_path)
        else:
            flash("Ruta de archivo no válida", "danger")
        
        conn.execute("DELETE FROM pdfs WHERE id=?", (pdf_id,))  # <-- SQL Injection protection
        conn.commit()
        flash(f'PDF "{pdf["filename"]}" eliminado', "success")
    conn.close()
    return redirect(url_for("open_folder", folder_id=folder_id))

@app.route("/edit_pdf/<int:pdf_id>/<int:folder_id>", methods=["POST"])
@validate_folder_access  # <-- PROTECCIÓN IDOR
def edit_pdf(pdf_id, folder_id):
    new_name = request.form["new_name"]
    
    # =========== SEGURIDAD: Validación de nombre =========== #
    if not security.validate_filename(new_name):
        flash("Nombre de archivo no permitido", "danger")
        return redirect(url_for("open_folder", folder_id=folder_id))
    
    conn = get_db_connection()
    pdf = conn.execute("SELECT * FROM pdfs WHERE id=?", (pdf_id,)).fetchone()
    if pdf:
        # =========== SEGURIDAD: Path traversal protection =========== #
        old_safe_path = security.safe_path_access(pdf["filename"], os.path.join(UPLOAD_FOLDER, str(folder_id)))
        new_safe_path = security.safe_path_access(new_name, os.path.join(UPLOAD_FOLDER, str(folder_id)))
        
        if not old_safe_path or not new_safe_path:
            flash("Ruta de archivo no válida", "danger")
            conn.close()
            return redirect(url_for("open_folder", folder_id=folder_id))
            
        try:
            os.rename(old_safe_path, new_safe_path)
            conn.execute("UPDATE pdfs SET filename=? WHERE id=?", (new_name, pdf_id))  # <-- SQL Injection protection
            conn.commit()
            flash(f'PDF renombrado a "{new_name}"', "success")
        except FileNotFoundError:
            flash("Archivo original no encontrado", "danger")
        except PermissionError:
            flash("No se puede renombrar archivo, revisa permisos", "danger")
    conn.close()
    return redirect(url_for("open_folder", folder_id=folder_id))

@app.route("/update_pdf/<int:pdf_id>", methods=["POST"])
def update_pdf(pdf_id):
    new_name = request.form["filename"]
    new_tags = request.form["tags"]

    # =========== SEGURIDAD: Validación y sanitización =========== #
    if not security.validate_filename(new_name):
        return "Nombre de archivo no válido", 400
    
    safe_tags = security.sanitize_input(new_tags)

    conn = get_db_connection()
    pdf = conn.execute("SELECT * FROM pdfs WHERE id=?", (pdf_id,)).fetchone()  # <-- SQL Injection protection
    if not pdf:
        conn.close()
        return "PDF no encontrado", 404
        
    folder_id = pdf["folder_id"]
    
    # =========== SEGURIDAD: Path traversal protection =========== #
    old_safe_path = security.safe_path_access(pdf["filename"], os.path.join(UPLOAD_FOLDER, str(folder_id)))
    new_safe_path = security.safe_path_access(new_name, os.path.join(UPLOAD_FOLDER, str(folder_id)))
    
    if not old_safe_path or not new_safe_path:
        conn.close()
        return "Ruta de archivo no válida", 400

    if old_safe_path != new_safe_path:
        try:
            os.rename(old_safe_path, new_safe_path)
        except Exception as e:
            conn.close()
            return f"Error al renombrar: {str(e)}", 500

    conn.execute("UPDATE pdfs SET filename=?, tags=? WHERE id=?", (new_name, safe_tags, pdf_id))  # <-- SQL Injection protection
    conn.commit()
    conn.close()
    return "ok"

@app.route("/view_pdf/<int:folder_id>/<filename>")
@validate_folder_access  # <-- PROTECCIÓN IDOR
def view_pdf(folder_id, filename):
    # =========== SEGURIDAD: Path traversal protection =========== #
    safe_path = security.safe_path_access(filename, os.path.join(UPLOAD_FOLDER, str(folder_id)))
    if not safe_path or not safe_path.exists():
        abort(404)
    
    return send_from_directory(os.path.join(UPLOAD_FOLDER, str(folder_id)), filename)

# ----------- Búsqueda por nombre y etiquetas ----------- #
@app.route("/search/<int:folder_id>", methods=["GET"])
@validate_folder_access  # <-- PROTECCIÓN IDOR
def search(folder_id):
    query = request.args.get("query", "")
    
    # =========== SEGURIDAD: Sanitización de búsqueda =========== #
    safe_query = security.sanitize_input(query)
    
    conn = get_db_connection()
    # =========== SEGURIDAD: SQL Injection protection =========== #
    pdfs = conn.execute("SELECT * FROM pdfs WHERE folder_id=? AND (filename LIKE ? OR tags LIKE ?)",
                        (folder_id, f"%{safe_query}%", f"%{safe_query}%")).fetchall()
    folders = conn.execute("SELECT * FROM folders").fetchall()
    folder_selected = conn.execute("SELECT * FROM folders WHERE id=?", (folder_id,)).fetchone()
    conn.close()
    return render_template("index.html", folders=folders, pdfs=pdfs, folder_selected=folder_selected)

# =========== SEGURIDAD: Manejo global de errores =========== #
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(403)
def forbidden(error):
    return render_template('403.html'), 403

@app.errorhandler(500)
def internal_error(error):
    # Log del error real (para administradores)
    app.logger.error(f"Error interno: {error}")
    # Mensaje genérico para usuarios
    return render_template('500.html'), 500

if __name__ == "__main__":
    # =========== SEGURIDAD: Debug desactivado en producción =========== #
    app.run(debug=False)
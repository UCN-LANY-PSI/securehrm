import os
import sqlite3
import subprocess
from pathlib import Path
from flask import Flask, request, redirect, url_for, render_template, send_file, flash
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "securehrm.db"
UPLOAD_DIR = BASE_DIR / "uploads"
FILES_DIR = BASE_DIR / "files"
BACKUP_DIR = BASE_DIR / "backups"

UPLOAD_DIR.mkdir(exist_ok=True)
FILES_DIR.mkdir(exist_ok=True)
BACKUP_DIR.mkdir(exist_ok=True)

app = Flask(__name__)
app.secret_key = "dev-secret-key"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.executescript(
        """
        DROP TABLE IF EXISTS employees;
        DROP TABLE IF EXISTS feedback;

        CREATE TABLE employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            email TEXT NOT NULL,
            salary INTEGER NOT NULL
        );

        CREATE TABLE feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            author TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

    employees = [
        ("Alice Hansen", "HR", "alice@securehrm.local", 48000),
        ("Bob Nielsen", "IT", "bob@securehrm.local", 56000),
        ("Carla Madsen", "Finance", "carla@securehrm.local", 59000),
        ("Daniel Sørensen", "IT", "daniel@securehrm.local", 53000),
        ("Emma Jensen", "HR", "emma@securehrm.local", 47000),
    ]
    cur.executemany(
        "INSERT INTO employees(name, department, email, salary) VALUES (?, ?, ?, ?)",
        employees,
    )

    feedback_entries = [
        ("Admin", "Velkommen til SecureHRM feedback-portalen."),
        ("QA", "Husk at teste inputfelter grundigt."),
    ]
    cur.executemany(
        "INSERT INTO feedback(author, message) VALUES (?, ?)",
        feedback_entries,
    )

    conn.commit()
    conn.close()

    (FILES_DIR / "policies.txt").write_text(
        "Internal HR policies\n- Password rotation\n- Access reviews\n- Least privilege\n",
        encoding="utf-8",
    )
    (FILES_DIR / "employees.csv").write_text(
        "id,name,department,email,salary\n"
        "1,Alice Hansen,HR,alice@securehrm.local,48000\n"
        "2,Bob Nielsen,IT,bob@securehrm.local,56000\n",
        encoding="utf-8",
    )


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/init")
def reset_demo():
    init_db()
    flash("Demo data nulstillet.")
    return redirect(url_for("index"))


@app.route("/reports", methods=["GET", "POST"])
def reports():
    department = request.values.get("department", "")
    query = None
    rows = []
    error = None

    if department:
        # Intentionally vulnerable to SQL injection
        query = (
            "SELECT id, name, department, email, salary "
            f"FROM employees WHERE department = '{department}'"
        )
        try:
            conn = get_db()
            rows = conn.execute(query).fetchall()
            conn.close()
        except Exception as exc:
            error = str(exc)

    return render_template(
        "reports.html",
        department=department,
        query=query,
        rows=rows,
        error=error,
    )


@app.route("/feedback", methods=["GET", "POST"])
def feedback():
    if request.method == "POST":
        author = request.form.get("author", "Anonymous")
        message = request.form.get("message", "")

        conn = get_db()
        conn.execute(
            "INSERT INTO feedback(author, message) VALUES (?, ?)",
            (author, message),
        )
        conn.commit()
        conn.close()
        return redirect(url_for("feedback"))

    conn = get_db()
    entries = conn.execute(
        "SELECT id, author, message, created_at FROM feedback ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return render_template("feedback.html", entries=entries)


@app.route("/upload", methods=["GET", "POST"])
def upload():
    uploaded_files = sorted(
        [p.name for p in UPLOAD_DIR.iterdir() if p.is_file()],
        reverse=True,
    )

    if request.method == "POST":
        file = request.files.get("document")
        if not file or not file.filename:
            flash("Vælg en fil.")
            return redirect(url_for("upload"))

        # Intentionally insecure: only normalizes filename, no validation of type/content
        filename = secure_filename(file.filename)
        destination = UPLOAD_DIR / filename
        file.save(destination)
        flash(f"Fil uploadet: {filename}")
        return redirect(url_for("upload"))

    return render_template("upload.html", uploaded_files=uploaded_files)


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_file(UPLOAD_DIR / filename)


@app.route("/backup", methods=["GET", "POST"])
def backup():
    target = request.values.get("target", "files")
    command = None
    output = None

    if request.method == "POST":
        archive_path = BACKUP_DIR / "backup.tar.gz"
        # Intentionally vulnerable to command injection through shell=True and string concatenation
        command = f"tar -czf {archive_path} {target}"
        try:
            completed = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=BASE_DIR,
            )
            output = (completed.stdout or "") + (completed.stderr or "")
            if not output.strip():
                output = "Backup command executed."
        except Exception as exc:
            output = str(exc)

    return render_template("backup.html", target=target, command=command, output=output)


@app.route("/download")
def download():
    filename = request.args.get("filename", "policies.txt")
    # Intentionally vulnerable to path traversal
    requested_path = os.path.join(FILES_DIR, filename)
    return send_file(requested_path, as_attachment=False)


@app.route("/crash")
def crash():
    value = int(request.args.get("value", "not-a-number"))
    return {"parsed": value}


if __name__ == "__main__":
    if not DB_PATH.exists():
        init_db()
    host = os.environ.get("FLASK_RUN_HOST", "0.0.0.0")
    port = int(os.environ.get("FLASK_RUN_PORT", "5000"))
    app.run(debug=True, host=host, port=port)

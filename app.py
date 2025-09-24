import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "segredo-super-forte"

DB_NAME = "database.db"

# Inicializa o banco
def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome TEXT NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        senha TEXT NOT NULL
                    )''')
        c.execute('''CREATE TABLE IF NOT EXISTS jovens (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome TEXT NOT NULL,
                        telefone TEXT,
                        email TEXT,
                        endereco TEXT,
                        data_nascimento TEXT
                    )''')
        conn.commit()

init_db()

# ---------- ROTAS ----------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        nome = request.form["nome"]
        email = request.form["email"]
        senha = generate_password_hash(request.form["senha"])
        try:
            with sqlite3.connect(DB_NAME) as conn:
                c = conn.cursor()
                c.execute("INSERT INTO users (nome, email, senha) VALUES (?, ?, ?)", (nome, email, senha))
                conn.commit()
            flash("Usuário cadastrado com sucesso!", "success")
            return redirect(url_for("login"))
        except:
            flash("E-mail já cadastrado!", "danger")
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        senha = request.form["senha"]
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT id, nome, senha FROM users WHERE email = ?", (email,))
            user = c.fetchone()
        if user and check_password_hash(user[2], senha):
            session["user_id"] = user[0]
            session["nome"] = user[1]
            return redirect(url_for("dashboard"))
        else:
            flash("E-mail ou senha inválidos!", "danger")
    return render_template("login.html")

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        nome = request.form["nome"]
        telefone = request.form["telefone"]
        email = request.form["email"]
        endereco = request.form["endereco"]
        nascimento = request.form["data_nascimento"]
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("INSERT INTO jovens (nome, telefone, email, endereco, data_nascimento) VALUES (?, ?, ?, ?, ?)",
                      (nome, telefone, email, endereco, nascimento))
            conn.commit()
        flash("Jovem cadastrado com sucesso!", "success")

    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM jovens")
        jovens = c.fetchall()

    return render_template("dashboard.html", jovens=jovens)

@app.route("/listar_jovens")
def listar_jovens():
    if "user_id" not in session:
        return redirect(url_for("login"))

    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM jovens")
        jovens = c.fetchall()
    return render_template("listar_jovens.html", jovens=jovens)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

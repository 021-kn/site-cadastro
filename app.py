from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback123")

DB_NAME = "database.db"

# -------------------- BANCO DE DADOS --------------------
def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jovens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            telefone TEXT,
            email TEXT,
            endereco TEXT,
            data_nascimento TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# -------------------- LOGIN --------------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        senha = request.form["senha"]

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT senha, nome FROM usuarios WHERE email=?", (email,))
        usuario = cursor.fetchone()
        conn.close()

        if usuario:
            senha_armazenada, nome = usuario
            if check_password_hash(senha_armazenada, senha):
                session["usuario"] = email
                session["nome"] = nome
                return redirect(url_for("dashboard"))
            else:
                flash("Senha incorreta!")
        else:
            flash("Usuário não encontrado!")

    return render_template("login.html")

# -------------------- REGISTER --------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        nome = request.form["nome"]
        email = request.form["email"]
        senha = generate_password_hash(request.form["senha"])

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)", (nome, email, senha))
            conn.commit()
            flash("Cadastro realizado com sucesso!")
            return redirect(url_for("login"))
        except:
            flash("E-mail já cadastrado!")
        finally:
            conn.close()

    return render_template("register.html")

# -------------------- DASHBOARD --------------------
@app.route("/dashboard")
def dashboard():
    if "usuario" not in session:
        return redirect(url_for("login"))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jovens")
    jovens = cursor.fetchall()
    conn.close()
    return render_template("dashboard.html", nome=session["nome"], jovens=jovens)

# -------------------- LOGOUT --------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# -------------------- DECORATOR LOGIN REQUIRED --------------------
def login_required(f):
    from functools import wraps
    @wraps(f)
    def wrap(*args, **kwargs):
        if "usuario" not in session:
            flash("Você precisa estar logado!")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrap

# -------------------- CADASTRO DE JOVENS --------------------
@app.route("/cadastrar_jovem", methods=["GET", "POST"])
@login_required
def cadastrar_jovem():
    if request.method == "POST":
        nome = request.form["nome"]
        telefone = request.form["telefone"]
        email = request.form["email"]
        endereco = request.form["endereco"]
        data_nascimento = request.form["data_nascimento"]

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO jovens (nome, telefone, email, endereco, data_nascimento)
            VALUES (?, ?, ?, ?, ?)
        """, (nome, telefone, email, endereco, data_nascimento))
        conn.commit()
        conn.close()

        flash("Jovem cadastrado com sucesso!")
        return redirect(url_for("listar_jovens"))

    return render_template("cadastrar_jovem.html")

# -------------------- LISTAR JOVENS --------------------
@app.route("/listar_jovens")
@login_required
def listar_jovens():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jovens")
    jovens = cursor.fetchall()
    conn.close()
    return render_template("listar_jovens.html", jovens=jovens)

# -------------------- RODAR APP --------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

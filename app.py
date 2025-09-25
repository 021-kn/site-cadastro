from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
import psycopg2.extras
import os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback123")

# URL do banco do Render (coloque essa variável no painel do Render)
DATABASE_URL = os.getenv("DATABASE_URL")

# -------------------- BANCO DE DADOS --------------------
def get_db_connection():
    return psycopg2.connect(DATABASE_URL, sslmode="require")

def init_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Cria tabelas apenas se não existirem
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                nome TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                senha TEXT NOT NULL,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jovens (
                id SERIAL PRIMARY KEY,
                nome TEXT NOT NULL,
                telefone TEXT,
                email TEXT,
                endereco TEXT,
                data_nascimento TEXT
            )
        """)
        conn.commit()
    except Exception as e:
        print("Erro ao inicializar o banco:", e)
    finally:
        if conn:
            cursor.close()
            conn.close()

# Inicializa as tabelas (não recria banco)
init_db()

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

# -------------------- LOGIN --------------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        senha = request.form["senha"]

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT senha, nome FROM usuarios WHERE email=%s", (email,))
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
            cursor.execute("INSERT INTO usuarios (nome, email, senha) VALUES (%s, %s, %s)", (nome, email, senha))
            conn.commit()
            flash("Cadastro realizado com sucesso!")
            return redirect(url_for("login"))
        except:
            flash("E-mail já cadastrado!")
        finally:
            cursor.close()
            conn.close()
    return render_template("register.html")

# -------------------- DASHBOARD --------------------
@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("SELECT * FROM jovens")
    jovens = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("dashboard.html", nome=session["nome"], jovens=jovens)

# -------------------- LOGOUT --------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

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
            VALUES (%s, %s, %s, %s, %s)
        """, (nome, telefone, email, endereco, data_nascimento))
        conn.commit()
        cursor.close()
        conn.close()

        flash("Jovem cadastrado com sucesso!")
        return redirect(url_for("dashboard"))

    return render_template("cadastrar_jovem.html")

# -------------------- LISTAR JOVENS --------------------
@app.route("/listar_jovens")
@login_required
def listar_jovens():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("SELECT * FROM jovens")
    jovens = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("listar_jovens.html", jovens=jovens)

# -------------------- EDITAR JOVEM --------------------
@app.route("/editar_jovem/<int:id>", methods=["GET", "POST"])
@login_required
def editar_jovem(id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("SELECT * FROM jovens WHERE id=%s", (id,))
    jovem = cursor.fetchone()

    if not jovem:
        cursor.close()
        conn.close()
        flash("Jovem não encontrado!")
        return redirect(url_for("listar_jovens"))

    if request.method == "POST":
        nome = request.form["nome"]
        telefone = request.form["telefone"]
        email = request.form["email"]
        endereco = request.form["endereco"]
        data_nascimento = request.form["data_nascimento"]

        cursor.execute("""
            UPDATE jovens
            SET nome=%s, telefone=%s, email=%s, endereco=%s, data_nascimento=%s
            WHERE id=%s
        """, (nome, telefone, email, endereco, data_nascimento, id))
        conn.commit()
        cursor.close()
        conn.close()
        flash("Jovem atualizado com sucesso!")
        return redirect(url_for("listar_jovens"))

    cursor.close()
    conn.close()
    return render_template("editar_jovem.html", jovem=jovem)

# -------------------- EXCLUIR JOVEM --------------------
@app.route("/excluir_jovem/<int:id>")
@login_required
def excluir_jovem(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM jovens WHERE id=%s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash("Jovem excluído com sucesso!")
    return redirect(url_for("listar_jovens"))

# -------------------- RODAR APP --------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
